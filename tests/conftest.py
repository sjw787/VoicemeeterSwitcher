"""Test doubles for Voicemeeter.

``voicemeeterlib`` cannot be imported off Windows -- ``inst.py`` imports
``winreg`` and raises ``InstallError`` on a platform check -- so these fakes
mirror only the surface ``VoicemeeterController`` actually touches:
``login()``, ``logout()``, ``bus[i].gain`` and ``bus[i].mute``.
"""

from __future__ import annotations

import pytest


class FakeDevice:
    """Mirrors ``bus[i].device`` / ``strip[i].device``.

    ``main.load_setting`` assigns by driver type, e.g.
    ``setattr(bus.device, 'wdm', 'Speakers (Yamaha SR-C20A)')``.
    """

    def __init__(self) -> None:
        self.mme: str | None = None
        self.ks: str | None = None
        self.wdm: str | None = None
        self.asio: str | None = None

    @property
    def assigned(self) -> str | None:
        """Whichever driver slot was last given a non-empty name."""
        for value in (self.mme, self.ks, self.wdm, self.asio):
            if value:
                return value
        return None


class FakeBus:
    """One Voicemeeter bus.

    Reads are served from a *snapshot*, not from the live value, mirroring
    ``VBVMR_GetParameterFloat``. The snapshot only catches up when the dirty
    flag is polled -- see :meth:`FakeRemote.pdirty`. Writes made through this
    object update both, since a client always sees its own writes.
    """

    def __init__(self, remote: "FakeRemote") -> None:
        self._remote = remote
        self._gain = 0.0
        self._mute = False
        #: What a read returns until the dirty flag is polled.
        self._snapshot_gain = 0.0
        self._snapshot_mute = False
        self.device = FakeDevice()

    def _publish(self) -> None:
        """Bring the read snapshot up to date with the live values."""
        self._snapshot_gain = self._gain
        self._snapshot_mute = self._mute

    @property
    def gain(self) -> float:
        self._remote.gain_reads += 1
        return self._snapshot_gain

    @gain.setter
    def gain(self, value: float) -> None:
        if self._remote.fail_writes:
            raise RuntimeError("simulated Voicemeeter write failure")
        self._remote.gain_writes.append(float(value))
        self._gain = float(value)
        self._snapshot_gain = float(value)

    @property
    def mute(self) -> bool:
        self._remote.mute_reads += 1
        return self._snapshot_mute

    @mute.setter
    def mute(self, value: bool) -> None:
        if self._remote.fail_writes:
            raise RuntimeError("simulated Voicemeeter write failure")
        self._remote.mute_writes.append(bool(value))
        self._mute = bool(value)
        self._snapshot_mute = bool(value)


class FakeStrip:
    """One Voicemeeter input strip. Only device assignment is exercised."""

    def __init__(self) -> None:
        self.device = FakeDevice()


class FakeRemote:
    """Stand-in for a logged-in ``voicemeeterlib`` remote."""

    def __init__(
        self, kind: str = "potato", num_buses: int = 8, num_strips: int = 8
    ) -> None:
        self.kind = kind
        self.bus = [FakeBus(self) for _ in range(num_buses)]
        self.strip = [FakeStrip() for _ in range(num_strips)]
        self.logins = 0
        self.logouts = 0
        self.gain_reads = 0
        self.mute_reads = 0
        self.gain_writes: list[float] = []
        self.mute_writes: list[bool] = []
        self.fail_writes = False
        #: voicemeeterlib's set-into-get memo. Present so code that inspects it
        #: does not trip over a missing attribute.
        self.cache: dict = {}
        self._dirty = False
        self.pdirty_polls = 0

    @property
    def pdirty(self) -> bool:
        """Mirrors ``VBVMR_IsParametersDirty``.

        Returns True once after something changed the values behind the
        snapshot, and *the act of polling refreshes the snapshot*. That is the
        real API's contract, and the reason a client that never polls can read
        a stale fader position indefinitely.
        """
        self.pdirty_polls += 1
        if not self._dirty:
            return False
        self._dirty = False
        for bus in self.bus:
            bus._publish()
        return True

    def seed(
        self, *, gain: float | None = None, mute: bool | None = None, index: int = 0
    ) -> None:
        """Set the state Voicemeeter was already in before anyone connected.

        Unlike :meth:`external_change`, this is immediately visible to reads --
        it represents the starting position, not a change made behind a
        client's back.
        """
        bus = self.bus[index]
        if gain is not None:
            bus._gain = float(gain)
            bus._snapshot_gain = float(gain)
        if mute is not None:
            bus._mute = bool(mute)
            bus._snapshot_mute = bool(mute)

    def external_change(
        self, *, gain: float | None = None, mute: bool | None = None, index: int = 0
    ) -> None:
        """Change values the way the Voicemeeter GUI or another client would.

        Updates the live value and raises the dirty flag, but deliberately does
        **not** touch the read snapshot -- exactly what was observed on real
        hardware.
        """
        bus = self.bus[index]
        if gain is not None:
            bus._gain = float(gain)
        if mute is not None:
            bus._mute = bool(mute)
        self._dirty = True

    def login(self) -> None:
        self.logins += 1

    def logout(self) -> None:
        self.logouts += 1


class FakeBackend:
    """Callable backend that hands out ``FakeRemote`` instances.

    Set ``fail_with`` to make the next connection attempt raise, simulating
    Voicemeeter not being running yet.
    """

    def __init__(self, remote: FakeRemote | None = None) -> None:
        self.remote = remote or FakeRemote()
        self.calls = 0
        self.fail_with: Exception | None = None

    def __call__(self, kind: str) -> FakeRemote:
        self.calls += 1
        if self.fail_with is not None:
            raise self.fail_with
        return self.remote


class FakeSwitcher:
    """Stand-in for ``VoicemeeterSettingsSwitcher``.

    Records the remote it was handed so tests can assert the controller passes
    a live connection through to the existing XML-applying code.
    """

    def __init__(self) -> None:
        self.loaded: list = []
        self.cycles = 0
        self.result = True
        self.seen_remotes: list = []
        #: Mutates gain on load, the way a real profile XML can.
        self.gain_after_load: float | None = None

    def _maybe_move_fader(self, remote) -> None:
        if self.gain_after_load is not None:
            # A real profile load moves the fader behind the API's back, so it
            # has to raise the dirty flag like any other external change.
            remote.external_change(gain=self.gain_after_load)

    def load_setting(self, remote, path) -> bool:
        self.seen_remotes.append(remote)
        self.loaded.append(path)
        self._maybe_move_fader(remote)
        return self.result

    def cycle_next(self, remote) -> bool:
        self.seen_remotes.append(remote)
        self.cycles += 1
        self._maybe_move_fader(remote)
        return self.result


class FakeClock:
    """Manually advanced monotonic clock, so interval logic needs no real sleeps."""

    def __init__(self) -> None:
        self.now = 1000.0
        self.slept: list[float] = []

    def monotonic(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.slept.append(seconds)
        self.now += seconds

    def advance(self, seconds: float) -> None:
        self.now += seconds


@pytest.fixture
def remote() -> FakeRemote:
    return FakeRemote()


@pytest.fixture
def backend(remote: FakeRemote) -> FakeBackend:
    return FakeBackend(remote)


@pytest.fixture
def switcher() -> FakeSwitcher:
    return FakeSwitcher()


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock()


@pytest.fixture
def controller(backend, switcher, clock):
    from controller import VoicemeeterController

    ctl = VoicemeeterController(
        switcher,
        kind="potato",
        backend=backend,
        monotonic=clock.monotonic,
        sleep=clock.sleep,
    )
    yield ctl
    ctl.close()
