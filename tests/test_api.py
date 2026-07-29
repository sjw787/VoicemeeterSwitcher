"""Endpoint tests.

``api.py`` is importable off Windows because the controller imports
``voicemeeterlib`` lazily. That lets the whole HTTP surface be exercised here
with a fake Voicemeeter behind it.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

import api
from controller import VoicemeeterController


@pytest.fixture
def client(backend, clock, monkeypatch):
    """A test client whose controller talks to a fake Voicemeeter.

    The real ``load_setting`` runs, XML parsing and all -- only its Voicemeeter
    settle delays are stubbed out, since those exist for the DLL's benefit and
    there is no DLL here.
    """
    import main

    monkeypatch.setattr(main.time, "sleep", lambda _seconds: None)

    fake = VoicemeeterController(
        api.switcher,
        backend=backend,
        monotonic=clock.monotonic,
        sleep=clock.sleep,
    )
    monkeypatch.setattr(api, "controller", fake)
    # Don't let tests scribble on the real .current_index state file.
    monkeypatch.setattr(api.switcher, "_save_index", lambda: None)
    original_index = api.switcher.current_index
    with TestClient(api.app) as test_client:
        yield test_client
    api.switcher.current_index = original_index
    fake.close()


class TestRoot:
    def test_lists_endpoints(self, client):
        body = client.get("/").json()
        assert body["name"] == "Voicemeeter Control API"
        assert "/api/volume/a1" in body["endpoints"]


class TestProfiles:
    def test_lists_the_four_real_profiles(self, client):
        body = client.get("/api/profiles").json()
        names = [p["display_name"] for p in body["profiles"]]
        assert names == ["DeskSettings", "Headset", "Soundbar", "TvSpeakers"]
        assert body["total"] == 4

    def test_display_name_strips_sort_prefix(self, client):
        body = client.get("/api/profiles").json()
        first = body["profiles"][0]
        assert first["filename"] == "1-DeskSettings.xml"
        assert first["display_name"] == "DeskSettings"

    def test_load_by_filename(self, client):
        response = client.post(
            "/api/profile/load", json={"profile_name": "3-Soundbar.xml"}
        )
        assert response.status_code == 200
        assert response.json()["message"] == "Loaded Soundbar"

    def test_load_actually_reassigns_the_a1_device(self, client, backend):
        """End to end: XML is parsed and the device lands on bus 0 (A1).

        ``3-Soundbar.xml`` declares ``OutputDev index='1' type='1'``, and
        type 1 is the MME driver.
        """
        client.post("/api/profile/load", json={"profile_name": "3-Soundbar.xml"})
        assert backend.remote.bus[0].device.mme == "Speakers (Yamaha SR-C20A)"

    def test_every_profile_targets_a1(self, client, backend):
        """The dial can hardcode bus 0 only because this holds for all four."""
        expected = {
            "1-DeskSettings.xml": "VA2756 Series (NVIDIA High Defi",
            "2-Headset.xml": "Headphones (5- Arctis Nova Pro ",
            "3-Soundbar.xml": "Speakers (Yamaha SR-C20A)",
            "4-TvSpeakers.xml": "GSV HDMI2.1 (NVIDIA High Defini",
        }
        for filename, device in expected.items():
            client.post("/api/profile/load", json={"profile_name": filename})
            assert backend.remote.bus[0].device.mme == device

    def test_load_unknown_profile_is_404(self, client):
        response = client.post(
            "/api/profile/load", json={"profile_name": "nope.xml"}
        )
        assert response.status_code == 404

    def test_cycle(self, client):
        response = client.post("/api/profile/cycle")
        assert response.status_code == 200
        assert response.json()["status"] == "success"


class TestStatus:
    def test_includes_voicemeeter_snapshot(self, client):
        body = client.get("/api/status").json()
        assert body["status"] == "running"
        assert body["total_profiles"] == 4
        assert "voicemeeter" in body
        assert body["voicemeeter"]["connected"] is False

    def test_polling_does_not_connect_to_voicemeeter(self, client, backend):
        for _ in range(20):
            client.get("/api/status")
        assert backend.calls == 0, "status polling must not touch the DLL"


class TestVolume:
    def test_set_and_get_absolute(self, client):
        assert client.post("/api/volume/a1", json={"gain": -6.0}).status_code == 200
        assert client.get("/api/volume/a1").json()["gain"] == -6.0

    def test_rejects_out_of_range(self, client):
        assert client.post("/api/volume/a1", json={"gain": 99.0}).status_code == 400
        assert client.post("/api/volume/a1", json={"gain": -99.0}).status_code == 400

    def test_accepts_exact_rails(self, client):
        assert client.post("/api/volume/a1", json={"gain": 12.0}).status_code == 200
        assert client.post("/api/volume/a1", json={"gain": -60.0}).status_code == 200

    def test_reports_503_when_voicemeeter_is_down(self, client, backend):
        backend.fail_with = RuntimeError("Voicemeeter not running")
        response = client.post("/api/volume/a1", json={"gain": -6.0})
        assert response.status_code == 503
        assert "not running" in response.json()["detail"]


class TestVolumeAdjust:
    """The dial's entry point."""

    def test_relative_change(self, client):
        client.post("/api/volume/a1", json={"gain": -10.0})
        body = client.post("/api/volume/a1/adjust", json={"delta_db": -1.5}).json()
        assert body["gain"] == -11.5
        assert body["delta_db"] == -1.5
        assert body["at_limit"] is False

    def test_accumulates_across_requests(self, client):
        client.post("/api/volume/a1", json={"gain": 0.0})
        for _ in range(10):
            response = client.post("/api/volume/a1/adjust", json={"delta_db": -1.5})
            assert response.status_code == 200
        assert client.get("/api/volume/a1").json()["gain"] == -15.0

    def test_positive_delta_raises_volume(self, client):
        client.post("/api/volume/a1", json={"gain": -20.0})
        body = client.post("/api/volume/a1/adjust", json={"delta_db": 2.0}).json()
        assert body["gain"] == -18.0

    def test_clamps_at_floor_and_flags_limit(self, client):
        client.post("/api/volume/a1", json={"gain": -59.0})
        body = client.post("/api/volume/a1/adjust", json={"delta_db": -5.0}).json()
        assert body["gain"] == -60.0
        assert body["at_limit"] is True

    def test_clamps_at_ceiling_and_flags_limit(self, client):
        client.post("/api/volume/a1", json={"gain": 11.0})
        body = client.post("/api/volume/a1/adjust", json={"delta_db": 5.0}).json()
        assert body["gain"] == 12.0
        assert body["at_limit"] is True

    def test_spinning_past_the_rail_does_not_drift(self, client):
        """Winding the dial down hard then back up one detent must move one detent."""
        client.post("/api/volume/a1", json={"gain": 0.0})
        for _ in range(60):
            client.post("/api/volume/a1/adjust", json={"delta_db": -1.5})
        assert client.get("/api/volume/a1").json()["gain"] == -60.0
        body = client.post("/api/volume/a1/adjust", json={"delta_db": 1.5}).json()
        assert body["gain"] == -58.5

    def test_rejects_absurd_delta(self, client):
        assert (
            client.post("/api/volume/a1/adjust", json={"delta_db": 500}).status_code
            == 400
        )

    def test_rejects_missing_field(self, client):
        assert client.post("/api/volume/a1/adjust", json={}).status_code == 422

    def test_503_when_voicemeeter_is_down(self, client, backend):
        backend.fail_with = RuntimeError("Voicemeeter not running")
        response = client.post("/api/volume/a1/adjust", json={"delta_db": -1.5})
        assert response.status_code == 503


class TestMute:
    def test_toggle_flips(self, client):
        assert client.post("/api/mute/a1/toggle").json()["muted"] is True
        assert client.post("/api/mute/a1/toggle").json()["muted"] is False

    def test_get_reflects_toggle(self, client):
        client.post("/api/mute/a1/toggle")
        assert client.get("/api/mute/a1").json()["muted"] is True

    def test_set_explicitly(self, client):
        assert client.post("/api/mute/a1", json={"muted": True}).json()["muted"] is True
        assert (
            client.post("/api/mute/a1", json={"muted": False}).json()["muted"] is False
        )

    def test_mute_does_not_disturb_gain(self, client):
        client.post("/api/volume/a1", json={"gain": -8.0})
        client.post("/api/mute/a1/toggle")
        assert client.get("/api/volume/a1").json()["gain"] == -8.0

    def test_503_when_voicemeeter_is_down(self, client, backend):
        backend.fail_with = RuntimeError("Voicemeeter not running")
        assert client.post("/api/mute/a1/toggle").status_code == 503


class TestHealth:
    def test_ok_even_when_voicemeeter_is_down(self, client, backend):
        """Connection-refused vs 200-with-disconnected is the distinction the
        dial bridge needs on a cold boot."""
        backend.fail_with = RuntimeError("Voicemeeter not running")
        body = client.get("/api/health").json()
        assert body["status"] == "ok"
        assert body["voicemeeter"]["connected"] is False

    def test_reports_profile_count(self, client):
        assert client.get("/api/health").json()["profiles"] == 4

    def test_does_not_touch_the_dll(self, client, backend):
        for _ in range(20):
            client.get("/api/health")
        assert backend.calls == 0
