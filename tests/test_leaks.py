"""Call after call must not grow file descriptors, threads or tasks (operator: RUN_LEAK=1)."""

import asyncio
import os
import threading

import pytest

from tests.test_controller import _run_outgoing

CALLS = int(os.environ.get("LEAK_CALLS", "30"))


def _fds() -> int:
    return len(os.listdir("/proc/self/fd"))


@pytest.mark.skipif(not os.environ.get("RUN_LEAK"), reason="slow; set RUN_LEAK=1")
async def test_many_calls_do_not_leak() -> None:
    samples: list[tuple[int, int, int]] = []
    for i in range(CALLS):
        ctl, _, _, phone, _ = await _run_outgoing()
        (sid,) = ctl.calls
        await ctl.end(sid, "success", notify=True)
        await phone.close()
        await asyncio.sleep(0.3)
        if i in (4, CALLS - 1):  # after warm-up, and at the end
            samples.append((_fds(), threading.active_count(), len(asyncio.all_tasks())))
    (fds0, threads0, tasks0), (fds1, threads1, tasks1) = samples
    print(
        f"calls={CALLS} fds {fds0}->{fds1} threads {threads0}->{threads1} tasks {tasks0}->{tasks1}"
    )
    assert fds1 <= fds0 + 3
    assert threads1 <= threads0 + 1
    assert tasks1 <= tasks0 + 3
