"""
Single owner of the Voicemeeter connection.

Two deliberately separate paths:

* **Fast path** (gain, mute) -- cheap parameter writes on an already-open
  connection with no artificial delay. Safe to drive from a rotary encoder
  that emits many events per second.
* **Slow path** (profile loads) -- reassigns hardware devices, which is what
  actually destabilises Voicemeeter. Serialised behind a mutex with a minimum
  interval between operations, exactly as before.

The connection is opened *lazily* and retried after failure. On a cold boot
this process will normally start before Voicemeeter does; "Voicemeeter is not
running yet" is a normal transient state, not a fatal error.

The Voicemeeter backend is injected rather than imported at module scope.
``import voicemeeterlib`` raises on non-Windows platforms (it imports
``winreg`` and hard-fails the platform check), so a module-level import would
make this file, and everything importing it, unimportable off Windows --
including in tests.
"""

from __future__ import annotations

import logging
import threading
import time
from contextlib import contextmanager
from typing import Any, Callable, Iterator, Optional

logger = logging.getLogger(__name__)

#: Every profile in ``settings/`` assigns its output device to ``OutputDev
#: index='1'``, so bus 0 is always the active output and the dial can target
#: it unconditionally.
A1_BUS_INDEX = 0

GAIN_MIN_DB = -60.0
GAIN_MAX_DB = 12.0

#: Minimum seconds between *device-reassigning* operations. Only ever applied
#: to the slow path.
DEFAULT_MIN_PROFILE_INTERVAL = 2.0

#: After a failed connection attempt, don't retry for this long. Without it a
#: dial spun while Voicemeeter is closed would hammer the DLL dozens of times
#: per second.
DEFAULT_CONNECT_RETRY_COOLDOWN = 2.0

#: How long a fast-path write waits for the DLL lock before giving up. Rotary
#: input is *discarded* rather than queued, so stale ticks can't land after a
#: profile switch completes.
DEFAULT_FAST_LOCK_TIMEOUT = 0.5

#: How many times to poll the Voicemeeter Remote dirty flag when resyncing.
#: ``voicemeeterlib.remote.clear_dirty()`` does this with an unbounded ``while``,
#: which is not safe inside a request handler, so the loop is capped.
DEFAULT_DIRTY_POLL_LIMIT = 8


class VoicemeeterUnavailable(RuntimeError):
    """Voicemeeter could not be reached (not running, or the DLL is missing)."""


class ProfileSwitchInProgress(RuntimeError):
    """A device-reassigning profile load is in flight; fast input was dropped."""


def clamp_gain(db: float) -> float:
    """Clamp a dB value to Voicemeeter's usable bus range."""
    return max(GAIN_MIN_DB, min(GAIN_MAX_DB, float(db)))


def _default_backend(kind: str) -> Any:
    """Create a real Voicemeeter remote. Imported lazily; Windows only."""
    import voicemeeterlib

    return voicemeeterlib.api(kind)


class VoicemeeterController:
    """Owns the Voicemeeter connection and the cached view of its state.

    Args:
        switcher: A ``VoicemeeterSettingsSwitcher``, which still owns profile
            discovery, index persistence and XML parsing.
        kind: Voicemeeter edition -- ``basic``, ``banana`` or ``potato``.
        backend: Callable taking ``kind`` and returning a remote object.
            Injected for tests; defaults to the real ``voicemeeterlib``.
        reconnect_per_operation: Fall back to the old behaviour of opening a
            fresh connection for every operation. Escape hatch in case one
            long-lived connection proves unstable in practice.
    """

    def __init__(
        self,
        switcher: Any,
        kind: str = "potato",
        *,
        backend: Optional[Callable[[str], Any]] = None,
        min_profile_interval: float = DEFAULT_MIN_PROFILE_INTERVAL,
        connect_retry_cooldown: float = DEFAULT_CONNECT_RETRY_COOLDOWN,
        fast_lock_timeout: float = DEFAULT_FAST_LOCK_TIMEOUT,
        dirty_poll_limit: int = DEFAULT_DIRTY_POLL_LIMIT,
        reconnect_per_operation: bool = False,
        monotonic: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._switcher = switcher
        self._kind = kind
        self._backend = backend or _default_backend
        self._min_profile_interval = min_profile_interval
        self._connect_retry_cooldown = connect_retry_cooldown
        self._fast_lock_timeout = fast_lock_timeout
        self._dirty_poll_limit = dirty_poll_limit
        self._reconnect_per_operation = reconnect_per_operation
        self._monotonic = monotonic
        self._sleep = sleep

        # Reentrant: the slow path holds this while calling helpers that
        # acquire it again.
        self._dll_lock = threading.RLock()
        self._state_lock = threading.Lock()

        self._remote: Any = None
        self._gain: Optional[float] = None
        self._mute: Optional[bool] = None
        self._switch_active = False
        self._last_operation_at: Optional[float] = None
        self._last_connect_failure_at: Optional[float] = None
        self._last_error: Optional[str] = None

    # ------------------------------------------------------------------
    # Connection lifecycle
    # ------------------------------------------------------------------

    @property
    def connected(self) -> bool:
        return self._remote is not None

    def _connect(self) -> Any:
        """Return the live connection, opening it on first use."""
        with self._dll_lock:
            if self._remote is not None:
                return self._remote

            now = self._monotonic()
            if (
                self._last_connect_failure_at is not None
                and now - self._last_connect_failure_at < self._connect_retry_cooldown
            ):
                raise VoicemeeterUnavailable(
                    f"Voicemeeter unavailable, not retrying yet: {self._last_error}"
                )

            remote = self._open()
            self._remote = remote
            logger.info("Connected to Voicemeeter (%s)", self._kind)

            # Prime the cache so reads never need to touch the DLL. A failure
            # here is not fatal -- the connection itself is good.
            try:
                self._refresh(remote)
            except Exception:  # pragma: no cover - defensive
                logger.warning("Could not prime state cache", exc_info=True)
            return remote

    def _open(self) -> Any:
        """Create and log in to a remote, recording failures for the cooldown."""
        try:
            remote = self._backend(self._kind)
            remote.login()
        except Exception as exc:
            self._last_connect_failure_at = self._monotonic()
            self._last_error = f"{type(exc).__name__}: {exc}"
            logger.warning("Voicemeeter connection failed: %s", self._last_error)
            raise VoicemeeterUnavailable(self._last_error) from exc

        self._last_connect_failure_at = None
        self._last_error = None
        return remote

    def _drop_connection(self) -> None:
        """Discard a connection that has started erroring, so the next call retries."""
        with self._dll_lock:
            remote, self._remote = self._remote, None
        if remote is None:
            return
        try:
            remote.logout()
        except Exception:  # pragma: no cover - best effort
            logger.debug("logout during connection drop failed", exc_info=True)

    def close(self) -> None:
        """Log out and forget the connection. Safe to call more than once."""
        self._drop_connection()

    @contextmanager
    def _session(self) -> Iterator[Any]:
        """Yield a usable remote, honouring ``reconnect_per_operation``."""
        if not self._reconnect_per_operation:
            yield self._connect()
            return

        remote = self._open()
        try:
            yield remote
        finally:
            try:
                remote.logout()
            except Exception:  # pragma: no cover - best effort
                logger.debug("logout after operation failed", exc_info=True)

    # ------------------------------------------------------------------
    # Fast path: gain and mute
    # ------------------------------------------------------------------

    @contextmanager
    def _fast_access(self) -> Iterator[Any]:
        """Guard a cheap parameter write, dropping input during a profile switch."""
        with self._state_lock:
            switching = self._switch_active
        if switching:
            raise ProfileSwitchInProgress("profile switch in flight; input dropped")

        if not self._dll_lock.acquire(timeout=self._fast_lock_timeout):
            raise ProfileSwitchInProgress("timed out waiting for the Voicemeeter lock")
        try:
            with self._session() as remote:
                try:
                    yield remote
                except VoicemeeterUnavailable:
                    raise
                except Exception:
                    # A write failing on an established connection usually
                    # means Voicemeeter went away underneath us.
                    self._drop_connection()
                    raise
        finally:
            self._dll_lock.release()

    def _sync_from_dll(self, remote: Any) -> None:
        """Make the DLL's parameter snapshot current before reading it.

        ``VBVMR_GetParameterFloat`` is served from a snapshot that only
        refreshes when the caller polls ``VBVMR_IsParametersDirty``. A process
        that never polls reads values frozen at its last poll, so a fader moved
        by the Voicemeeter GUI or by another client is *invisible* -- no amount
        of re-reading will show it.

        Verified on real hardware 2026-07-30: a separate process set A1 to
        -30.0 dB, Voicemeeter's own UI showed -30.0, and this service kept
        returning -24.0 across repeated forced reads until the flag was polled.

        ``voicemeeterlib`` exposes this as ``sync=True`` on the constructor, but
        its ``polling`` decorator checks its own set-into-get memo *before* the
        sync branch, so enabling sync alone would not be enough after a local
        write. Polling here is explicit and bounded.
        """
        try:
            for _ in range(self._dirty_poll_limit):
                if not remote.pdirty:
                    return
        except AttributeError:
            # Older or stubbed remotes may not expose the flag; a plain read is
            # still correct, just possibly stale.
            return
        except Exception:  # pragma: no cover - defensive
            logger.debug("polling the dirty flag failed", exc_info=True)

    def _refresh(self, remote: Any) -> None:
        """Re-read gain and mute from Voicemeeter into the cache."""
        self._sync_from_dll(remote)
        bus = remote.bus[A1_BUS_INDEX]
        gain = float(bus.gain)
        mute = bool(bus.mute)
        with self._state_lock:
            self._gain = gain
            self._mute = mute

    def resync(self) -> None:
        """Re-read cached state from Voicemeeter.

        Called after a profile load, which can move the fader out from under
        the cache.
        """
        with self._fast_access() as remote:
            self._refresh(remote)

    def get_gain(self, force_refresh: bool = False) -> float:
        """Current A1 gain in dB, from cache unless a refresh is demanded."""
        if not force_refresh:
            with self._state_lock:
                if self._gain is not None:
                    return self._gain
        with self._fast_access() as remote:
            self._refresh(remote)
        with self._state_lock:
            assert self._gain is not None
            return self._gain

    def set_gain(self, db: float) -> float:
        """Set A1 gain to an absolute dB value. Returns the clamped value."""
        target = clamp_gain(db)
        with self._fast_access() as remote:
            remote.bus[A1_BUS_INDEX].gain = target
            with self._state_lock:
                self._gain = target
        return target

    def adjust_gain(self, delta_db: float) -> float:
        """Move A1 gain by ``delta_db``. Returns the new clamped value.

        This is the dial's entry point: relative, single round trip, no
        read-modify-write race with the web UI.
        """
        with self._fast_access() as remote:
            with self._state_lock:
                current = self._gain
            if current is None:
                current = float(remote.bus[A1_BUS_INDEX].gain)
            target = clamp_gain(current + float(delta_db))
            remote.bus[A1_BUS_INDEX].gain = target
            with self._state_lock:
                self._gain = target
        return target

    def get_mute(self, force_refresh: bool = False) -> bool:
        """Current A1 mute state, from cache unless a refresh is demanded."""
        if not force_refresh:
            with self._state_lock:
                if self._mute is not None:
                    return self._mute
        with self._fast_access() as remote:
            self._refresh(remote)
        with self._state_lock:
            assert self._mute is not None
            return self._mute

    def set_mute(self, muted: bool) -> bool:
        """Set A1 mute state explicitly."""
        target = bool(muted)
        with self._fast_access() as remote:
            remote.bus[A1_BUS_INDEX].mute = target
            with self._state_lock:
                self._mute = target
        return target

    def toggle_mute(self) -> bool:
        """Flip A1 mute. Returns the new state."""
        with self._fast_access() as remote:
            with self._state_lock:
                current = self._mute
            if current is None:
                current = bool(remote.bus[A1_BUS_INDEX].mute)
            target = not current
            remote.bus[A1_BUS_INDEX].mute = target
            with self._state_lock:
                self._mute = target
        return target

    # ------------------------------------------------------------------
    # Slow path: profile loads
    # ------------------------------------------------------------------

    def _respect_min_interval(self) -> None:
        if self._last_operation_at is None:
            return
        elapsed = self._monotonic() - self._last_operation_at
        remaining = self._min_profile_interval - elapsed
        if remaining > 0:
            logger.debug("Waiting %.1fs before next device operation", remaining)
            self._sleep(remaining)

    @contextmanager
    def _slow_access(self) -> Iterator[Any]:
        """Guard a device-reassigning operation: mutex, interval floor, drop flag."""
        with self._dll_lock:
            self._respect_min_interval()
            with self._state_lock:
                self._switch_active = True
            try:
                with self._session() as remote:
                    yield remote
            finally:
                with self._state_lock:
                    self._switch_active = False
                self._last_operation_at = self._monotonic()

    def load_profile(self, profile_path: Any) -> bool:
        """Load a profile by path. Reassigns devices, so this is the slow path."""
        with self._slow_access() as remote:
            ok = bool(self._switcher.load_setting(remote, profile_path))
        if ok:
            self._resync_quietly()
        return ok

    def cycle_next(self) -> bool:
        """Advance to the next profile."""
        with self._slow_access() as remote:
            ok = bool(self._switcher.cycle_next(remote))
        if ok:
            self._resync_quietly()
        return ok

    def _resync_quietly(self) -> None:
        """Refresh the cache, tolerating failure -- the profile load succeeded."""
        try:
            self.resync()
        except Exception:
            logger.warning("Could not resync state after profile load", exc_info=True)

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    def snapshot(self) -> dict:
        """Cached state. Never touches the DLL, so it is safe to poll."""
        with self._state_lock:
            return {
                "connected": self._remote is not None,
                "kind": self._kind,
                "gain": self._gain,
                "mute": self._mute,
                "profile_switch_in_flight": self._switch_active,
                "reconnect_per_operation": self._reconnect_per_operation,
                "last_error": self._last_error,
            }
