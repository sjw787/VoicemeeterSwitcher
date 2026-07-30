"""
Voicemeeter Control API.

All Voicemeeter access goes through :class:`controller.VoicemeeterController`,
which owns a single lazily-opened connection and separates cheap parameter
writes (gain, mute) from device-reassigning profile loads. See the module
docstring in ``controller.py`` for why that split exists.

Note there is no module-level ``import voicemeeterlib`` here: the controller
imports it lazily so this module stays importable -- and testable -- off
Windows.
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager, contextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from controller import (
    GAIN_MAX_DB,
    GAIN_MIN_DB,
    ProfileSwitchInProgress,
    VoicemeeterController,
    VoicemeeterUnavailable,
)
from main import VoicemeeterSettingsSwitcher


def _env_flag(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.environ[name])
    except (KeyError, ValueError):
        return default


switcher = VoicemeeterSettingsSwitcher()

controller = VoicemeeterController(
    switcher,
    kind=os.environ.get("VMSW_KIND", "potato"),
    min_profile_interval=_env_float("VMSW_MIN_PROFILE_INTERVAL", 2.0),
    reconnect_per_operation=_env_flag("VMSW_RECONNECT_PER_OPERATION"),
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    controller.close()


app = FastAPI(title="Voicemeeter Control API", lifespan=lifespan)

# Enable CORS for phone access.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ProfileRequest(BaseModel):
    profile_name: str


class VolumeRequest(BaseModel):
    gain: float = Field(..., description="Absolute volume in dB")


#: A single dial detent is a couple of dB, so anything approaching a
#: full-range sweep in one request is a caller bug, not a gesture.
MAX_DELTA_DB = 72.0


class VolumeAdjustRequest(BaseModel):
    delta_db: float = Field(
        ...,
        description="Relative change in dB. Negative lowers the volume.",
    )


class MuteRequest(BaseModel):
    muted: bool


@contextmanager
def translate_errors():
    """Map controller failures onto HTTP status codes.

    503 means "Voicemeeter isn't reachable right now" -- expected on a cold
    boot before Voicemeeter has started, and retryable. 409 means a device
    switch is in flight and the input was deliberately dropped.
    """
    try:
        yield
    except VoicemeeterUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ProfileSwitchInProgress as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


def display_name(path: Path) -> str:
    """Strip the sort-order prefix: ``2-Headset.xml`` -> ``Headset``."""
    stem = path.stem
    if stem and stem[0].isdigit() and "-" in stem:
        return stem.split("-", 1)[1]
    return stem


def find_profile(profile_name: str) -> tuple[int, Path]:
    for index, path in enumerate(switcher.settings_files):
        if path.name == profile_name:
            return index, path
    raise HTTPException(
        status_code=404, detail=f"Profile not found: {profile_name}"
    )


@app.get("/")
def root():
    """API root endpoint."""
    return {
        "name": "Voicemeeter Control API",
        "version": "1.0",
        "endpoints": [
            "/api/profiles",
            "/api/profile/load",
            "/api/profile/cycle",
            "/api/status",
            "/api/health",
            "/api/volume/a1",
            "/api/volume/a1/adjust",
            "/api/mute/a1",
            "/api/mute/a1/toggle",
        ],
    }


@app.get("/api/profiles")
def get_profiles():
    """Get list of available profiles."""
    profiles = [
        {
            "filename": path.name,
            "display_name": display_name(path),
            "index": index,
        }
        for index, path in enumerate(switcher.settings_files)
    ]
    return {
        "profiles": profiles,
        "current_index": switcher.current_index,
        "total": len(profiles),
    }


@app.post("/api/profile/load")
def load_profile(request: ProfileRequest):
    """Load a specific profile by filename."""
    print(f"\nReceived request to load profile: {request.profile_name}")
    index, path = find_profile(request.profile_name)
    print(f"Found profile at index {index}: {path.name}")

    switcher.current_index = index
    switcher._save_index()

    with translate_errors():
        ok = controller.load_profile(path)

    if not ok:
        raise HTTPException(
            status_code=500,
            detail="Failed to load profile - check Voicemeeter is running",
        )

    name = display_name(path)
    print(f"Successfully loaded profile: {name}\n")
    return {
        "status": "success",
        "message": f"Loaded {name}",
        "profile": request.profile_name,
    }


@app.post("/api/profile/cycle")
def cycle_profile():
    """Cycle to the next profile."""
    print("\nReceived request to cycle profile")

    with translate_errors():
        ok = controller.cycle_next()

    if not ok:
        raise HTTPException(status_code=500, detail="Failed to cycle profile")

    current = switcher.settings_files[switcher.current_index]
    name = display_name(current)
    print(f"Cycled to profile: {name}\n")
    return {
        "status": "success",
        "message": f"Switched to {name}",
        "current_profile": current.name,
        "current_index": switcher.current_index,
    }


@app.get("/api/status")
def get_status():
    """Get current status. Served from cache, so it is safe to poll."""
    if not switcher.settings_files:
        return {
            "status": "running",
            "current_profile": None,
            "message": "No profiles available",
        }

    current = switcher.settings_files[switcher.current_index]
    snapshot = controller.snapshot()
    return {
        "status": "running",
        "current_profile": current.name,
        "current_display_name": display_name(current),
        "current_index": switcher.current_index,
        "total_profiles": len(switcher.settings_files),
        "settings_dir": str(switcher.settings_dir),
        "voicemeeter": snapshot,
    }


@app.get("/api/volume/a1")
def get_a1_volume(refresh: bool = False):
    """Get current A1 output volume in dB.

    Served from the cached view by default, which is why it is cheap enough to
    poll. Pass ``?refresh=true`` to re-read Voicemeeter instead.

    The cache is only corrected when the connection opens and after a profile
    load, so anything that moves the fader behind this service's back -- the
    Voicemeeter GUI, a second client, a Stream Deck macro -- leaves it stale.
    A relative controller such as a dial should refresh once before its first
    adjustment after an idle period, otherwise it computes its delta from a
    stale base and the volume jumps.
    """
    with translate_errors():
        gain = controller.get_gain(force_refresh=refresh)
    return {"bus": "A1", "gain": gain, "bus_index": 0, "refreshed": refresh}


@app.post("/api/volume/a1")
def set_a1_volume(request: VolumeRequest):
    """Set A1 output volume to an absolute dB value."""
    if request.gain < GAIN_MIN_DB or request.gain > GAIN_MAX_DB:
        raise HTTPException(
            status_code=400,
            detail=f"Gain must be between {GAIN_MIN_DB} and {GAIN_MAX_DB} dB",
        )

    print(f"\nReceived request to set A1 volume to {request.gain} dB")
    with translate_errors():
        gain = controller.set_gain(request.gain)

    print(f"Successfully set A1 volume to {gain} dB\n")
    return {
        "status": "success",
        "message": f"Set A1 volume to {gain} dB",
        "bus": "A1",
        "gain": gain,
    }


@app.post("/api/volume/a1/adjust")
def adjust_a1_volume(request: VolumeAdjustRequest):
    """Move A1 volume by a relative amount.

    This is the dial's entry point. Relative rather than absolute because a
    rotary encoder only knows "one detent clockwise", and because
    read-then-write from the caller would race the web UI.
    """
    if abs(request.delta_db) > MAX_DELTA_DB:
        raise HTTPException(
            status_code=400,
            detail=f"delta_db must be within +/-{MAX_DELTA_DB} dB",
        )

    with translate_errors():
        gain = controller.adjust_gain(request.delta_db)

    return {
        "status": "success",
        "bus": "A1",
        "gain": gain,
        "delta_db": request.delta_db,
        "at_limit": gain in (GAIN_MIN_DB, GAIN_MAX_DB),
    }


@app.get("/api/mute/a1")
def get_a1_mute(refresh: bool = False):
    """Get current A1 mute state.

    Cached by default; ``?refresh=true`` re-reads Voicemeeter. Same staleness
    caveat as the gain endpoint.
    """
    with translate_errors():
        muted = controller.get_mute(force_refresh=refresh)
    return {"bus": "A1", "muted": muted, "refreshed": refresh}


@app.post("/api/mute/a1")
def set_a1_mute(request: MuteRequest):
    """Set A1 mute state explicitly."""
    with translate_errors():
        muted = controller.set_mute(request.muted)
    return {"status": "success", "bus": "A1", "muted": muted}


@app.post("/api/mute/a1/toggle")
def toggle_a1_mute():
    """Flip A1 mute. Bound to the buttons 1+2 chord on the dial."""
    with translate_errors():
        muted = controller.toggle_mute()

    print(f"A1 {'muted' if muted else 'unmuted'}")
    return {"status": "success", "bus": "A1", "muted": muted}


@app.get("/api/health")
def health():
    """Liveness probe.

    Always 200 if the HTTP server is up, so a client can distinguish "the API
    isn't running yet" (connection refused) from "the API is up but Voicemeeter
    isn't" (``voicemeeter.connected`` false). The dial bridge polls this on
    startup, since on a cold boot it may well come up first.
    """
    return {
        "status": "ok",
        "profiles": len(switcher.settings_files),
        "voicemeeter": controller.snapshot(),
    }
