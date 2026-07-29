"""Tests for VoicemeeterController.

These run anywhere: the Voicemeeter backend is injected, so no DLL and no
Windows required.
"""

from __future__ import annotations

import threading

import pytest

from controller import (
    GAIN_MAX_DB,
    GAIN_MIN_DB,
    ProfileSwitchInProgress,
    VoicemeeterController,
    VoicemeeterUnavailable,
    clamp_gain,
)


class TestClampGain:
    def test_passes_through_in_range(self):
        assert clamp_gain(-12.5) == -12.5

    def test_clamps_both_rails(self):
        assert clamp_gain(-999) == GAIN_MIN_DB
        assert clamp_gain(999) == GAIN_MAX_DB

    def test_accepts_exact_rails(self):
        assert clamp_gain(GAIN_MIN_DB) == GAIN_MIN_DB
        assert clamp_gain(GAIN_MAX_DB) == GAIN_MAX_DB


class TestLazyConnection:
    def test_does_not_connect_until_first_use(self, controller, backend):
        assert backend.calls == 0
        assert controller.connected is False

    def test_connects_on_first_operation(self, controller, backend, remote):
        controller.set_gain(-6.0)
        assert backend.calls == 1
        assert remote.logins == 1
        assert controller.connected is True

    def test_reuses_one_connection(self, controller, backend, remote):
        for _ in range(25):
            controller.adjust_gain(-0.5)
        assert backend.calls == 1
        assert remote.logins == 1
        assert remote.logouts == 0

    def test_voicemeeter_not_running_is_not_fatal(self, controller, backend, clock):
        backend.fail_with = RuntimeError("Voicemeeter not running")
        with pytest.raises(VoicemeeterUnavailable):
            controller.set_gain(-6.0)

        # Recovers once Voicemeeter appears, after the cooldown elapses.
        backend.fail_with = None
        clock.advance(5.0)
        assert controller.set_gain(-6.0) == -6.0
        assert controller.connected is True

    def test_failed_connect_backs_off(self, controller, backend):
        backend.fail_with = RuntimeError("Voicemeeter not running")
        for _ in range(20):
            with pytest.raises(VoicemeeterUnavailable):
                controller.adjust_gain(-1.0)
        # Without the cooldown this would be 20 attempts against the DLL.
        assert backend.calls == 1

    def test_cooldown_expires(self, controller, backend, clock):
        backend.fail_with = RuntimeError("nope")
        with pytest.raises(VoicemeeterUnavailable):
            controller.adjust_gain(-1.0)
        clock.advance(2.5)
        with pytest.raises(VoicemeeterUnavailable):
            controller.adjust_gain(-1.0)
        assert backend.calls == 2

    def test_close_logs_out(self, controller, remote):
        controller.set_gain(0.0)
        controller.close()
        assert remote.logouts == 1
        assert controller.connected is False

    def test_close_is_idempotent(self, controller, remote):
        controller.set_gain(0.0)
        controller.close()
        controller.close()
        assert remote.logouts == 1

    def test_write_failure_drops_connection_for_retry(self, controller, remote):
        controller.set_gain(-6.0)
        remote.fail_writes = True
        with pytest.raises(RuntimeError):
            controller.set_gain(-3.0)
        assert controller.connected is False

        remote.fail_writes = False
        assert controller.set_gain(-3.0) == -3.0


class TestPerOperationFallback:
    """The escape hatch, in case one long-lived connection misbehaves."""

    def test_opens_and_closes_each_time(self, backend, switcher, clock):
        ctl = VoicemeeterController(
            switcher,
            backend=backend,
            reconnect_per_operation=True,
            monotonic=clock.monotonic,
            sleep=clock.sleep,
        )
        ctl.set_gain(-6.0)
        ctl.set_gain(-7.0)
        assert backend.calls == 2
        assert backend.remote.logins == 2
        assert backend.remote.logouts == 2

    def test_still_applies_gain(self, backend, switcher, clock):
        ctl = VoicemeeterController(
            switcher,
            backend=backend,
            reconnect_per_operation=True,
            monotonic=clock.monotonic,
            sleep=clock.sleep,
        )
        assert ctl.set_gain(-9.0) == -9.0
        assert backend.remote.bus[0]._gain == -9.0


class TestGain:
    def test_set_returns_clamped_value(self, controller):
        assert controller.set_gain(99.0) == GAIN_MAX_DB
        assert controller.set_gain(-99.0) == GAIN_MIN_DB

    def test_set_writes_to_bus_zero(self, controller, remote):
        controller.set_gain(-6.0)
        assert remote.bus[0]._gain == -6.0
        assert remote.gain_writes == [-6.0]

    def test_adjust_accumulates(self, controller):
        controller.set_gain(-10.0)
        assert controller.adjust_gain(-1.5) == -11.5
        assert controller.adjust_gain(-1.5) == -13.0
        assert controller.adjust_gain(3.0) == -10.0

    def test_adjust_clamps_at_ceiling_without_overshoot(self, controller):
        controller.set_gain(GAIN_MAX_DB - 1.0)
        assert controller.adjust_gain(5.0) == GAIN_MAX_DB
        assert controller.adjust_gain(5.0) == GAIN_MAX_DB

    def test_adjust_clamps_at_floor(self, controller):
        controller.set_gain(GAIN_MIN_DB + 1.0)
        assert controller.adjust_gain(-5.0) == GAIN_MIN_DB
        assert controller.adjust_gain(-5.0) == GAIN_MIN_DB

    def test_dial_spin_lands_on_expected_value(self, controller):
        """20 detents down at 1.5 dB, the realistic dial workload."""
        controller.set_gain(0.0)
        for _ in range(20):
            controller.adjust_gain(-1.5)
        assert controller.get_gain() == -30.0

    def test_adjust_reads_from_cache_not_the_dll(self, controller, remote):
        controller.set_gain(-10.0)
        reads_before = remote.gain_reads
        for _ in range(10):
            controller.adjust_gain(-1.0)
        assert remote.gain_reads == reads_before

    def test_adjust_reads_hardware_when_cache_is_cold(self, backend, switcher, clock):
        """No prior write, so the first adjust must establish a real baseline."""
        backend.remote.bus[0]._gain = -20.0
        ctl = VoicemeeterController(
            switcher, backend=backend, monotonic=clock.monotonic, sleep=clock.sleep
        )
        assert ctl.adjust_gain(-1.0) == -21.0

    def test_get_gain_is_cached(self, controller, remote):
        controller.set_gain(-6.0)
        reads_before = remote.gain_reads
        for _ in range(50):
            controller.get_gain()
        assert remote.gain_reads == reads_before

    def test_force_refresh_rereads_hardware(self, controller, remote):
        controller.set_gain(-6.0)
        remote.bus[0]._gain = -22.0  # changed behind our back
        assert controller.get_gain() == -6.0
        assert controller.get_gain(force_refresh=True) == -22.0


class TestMute:
    def test_toggle_flips_state(self, controller):
        assert controller.toggle_mute() is True
        assert controller.toggle_mute() is False

    def test_toggle_writes_to_bus_zero(self, controller, remote):
        controller.toggle_mute()
        assert remote.bus[0]._mute is True
        assert remote.mute_writes == [True]

    def test_set_mute_explicit(self, controller):
        assert controller.set_mute(True) is True
        assert controller.get_mute() is True
        assert controller.set_mute(False) is False

    def test_toggle_reads_hardware_when_cache_is_cold(self, backend, switcher, clock):
        backend.remote.bus[0]._mute = True
        ctl = VoicemeeterController(
            switcher, backend=backend, monotonic=clock.monotonic, sleep=clock.sleep
        )
        assert ctl.toggle_mute() is False

    def test_get_mute_is_cached(self, controller, remote):
        controller.set_mute(True)
        reads_before = remote.mute_reads
        for _ in range(50):
            controller.get_mute()
        assert remote.mute_reads == reads_before


class TestFastPathHasNoArtificialDelay:
    def test_no_sleeps_for_gain_or_mute(self, controller, clock):
        for _ in range(30):
            controller.adjust_gain(-0.5)
        controller.toggle_mute()
        controller.set_gain(-6.0)
        assert clock.slept == [], "fast path must never sleep"


class TestSlowPath:
    def test_load_profile_passes_live_remote_to_switcher(
        self, controller, switcher, remote
    ):
        assert controller.load_profile("1-DeskSettings.xml") is True
        assert switcher.loaded == ["1-DeskSettings.xml"]
        assert switcher.seen_remotes == [remote]

    def test_cycle_next_delegates(self, controller, switcher):
        assert controller.cycle_next() is True
        assert switcher.cycles == 1

    def test_failed_load_is_reported(self, controller, switcher):
        switcher.result = False
        assert controller.load_profile("bad.xml") is False

    def test_first_operation_does_not_wait(self, controller, clock):
        controller.load_profile("1-DeskSettings.xml")
        assert clock.slept == []

    def test_consecutive_loads_respect_interval_floor(self, controller, clock):
        controller.load_profile("1-DeskSettings.xml")
        controller.load_profile("2-Headset.xml")
        assert clock.slept == [pytest.approx(2.0)]

    def test_interval_floor_not_applied_once_elapsed(self, controller, clock):
        controller.load_profile("1-DeskSettings.xml")
        clock.advance(3.0)
        controller.load_profile("2-Headset.xml")
        assert clock.slept == []

    def test_gain_writes_do_not_trip_the_interval_floor(self, controller, clock):
        """The old code made every call wait 2s. Gain must be exempt."""
        controller.set_gain(-6.0)
        controller.load_profile("1-DeskSettings.xml")
        assert clock.slept == []

    def test_resyncs_cache_after_load(self, controller, switcher):
        """A profile load can move the fader; the cache must not go stale."""
        controller.set_gain(-6.0)
        switcher.gain_after_load = -18.0
        controller.load_profile("2-Headset.xml")
        assert controller.get_gain() == -18.0

    def test_resync_failure_does_not_fail_the_load(self, controller, switcher, remote):
        controller.set_gain(-6.0)

        original = type(remote.bus[0]).gain

        class Exploding:
            def __get__(self, obj, objtype=None):
                raise RuntimeError("read blew up")

        try:
            type(remote.bus[0]).gain = Exploding()
            assert controller.load_profile("2-Headset.xml") is True
        finally:
            type(remote.bus[0]).gain = original


class TestRotaryInputIsDroppedDuringProfileSwitch:
    """Stale dial ticks must not land after a device switch finishes."""

    def test_adjust_raises_while_switch_in_flight(self, backend, switcher, clock):
        started = threading.Event()
        release = threading.Event()
        outcome: dict = {}

        def blocking_load(remote, path):
            started.set()
            release.wait(timeout=5)
            return True

        switcher.load_setting = blocking_load

        ctl = VoicemeeterController(
            switcher,
            backend=backend,
            fast_lock_timeout=0.05,
            monotonic=clock.monotonic,
            sleep=clock.sleep,
        )

        loader = threading.Thread(target=ctl.load_profile, args=("1-Desk.xml",))
        loader.start()
        try:
            assert started.wait(timeout=5)
            with pytest.raises(ProfileSwitchInProgress):
                ctl.adjust_gain(-1.5)
            outcome["dropped"] = True
        finally:
            release.set()
            loader.join(timeout=5)

        assert outcome.get("dropped") is True
        # Accepts input again once the switch is done.
        assert isinstance(ctl.adjust_gain(-1.5), float)

    def test_snapshot_reports_switch_in_flight(self, backend, switcher, clock):
        started = threading.Event()
        release = threading.Event()
        seen: dict = {}

        def blocking_load(remote, path):
            started.set()
            release.wait(timeout=5)
            return True

        switcher.load_setting = blocking_load
        ctl = VoicemeeterController(
            switcher, backend=backend, monotonic=clock.monotonic, sleep=clock.sleep
        )

        loader = threading.Thread(target=ctl.load_profile, args=("1-Desk.xml",))
        loader.start()
        try:
            assert started.wait(timeout=5)
            seen["snapshot"] = ctl.snapshot()
        finally:
            release.set()
            loader.join(timeout=5)

        assert seen["snapshot"]["profile_switch_in_flight"] is True
        assert ctl.snapshot()["profile_switch_in_flight"] is False


class TestSnapshot:
    def test_reports_disconnected_before_first_use(self, controller):
        snap = controller.snapshot()
        assert snap["connected"] is False
        assert snap["gain"] is None
        assert snap["mute"] is None

    def test_reports_cached_state(self, controller):
        controller.set_gain(-6.0)
        controller.set_mute(True)
        snap = controller.snapshot()
        assert snap["connected"] is True
        assert snap["gain"] == -6.0
        assert snap["mute"] is True
        assert snap["kind"] == "potato"

    def test_never_touches_the_dll(self, controller, remote):
        controller.set_gain(-6.0)
        reads_before = (remote.gain_reads, remote.mute_reads)
        for _ in range(100):
            controller.snapshot()
        assert (remote.gain_reads, remote.mute_reads) == reads_before

    def test_records_last_error(self, controller, backend):
        backend.fail_with = RuntimeError("Voicemeeter not running")
        with pytest.raises(VoicemeeterUnavailable):
            controller.set_gain(-6.0)
        assert "Voicemeeter not running" in controller.snapshot()["last_error"]


class TestThreadSafety:
    def test_concurrent_adjusts_do_not_lose_writes(self, controller):
        controller.set_gain(0.0)
        errors: list = []

        def spin():
            try:
                for _ in range(50):
                    controller.adjust_gain(-0.1)
            except Exception as exc:  # pragma: no cover
                errors.append(exc)

        threads = [threading.Thread(target=spin) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10)

        assert errors == []
        # 200 decrements of 0.1 dB from 0.0, clamped at the floor.
        assert controller.get_gain() == pytest.approx(-20.0)
