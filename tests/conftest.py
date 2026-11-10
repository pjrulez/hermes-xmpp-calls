"""Shared fixtures for the call engine tests."""

import asyncio
import gc
import warnings

import pytest_asyncio


@pytest_asyncio.fixture(autouse=True)
async def _let_transports_close():
    """asyncio closes a transport's socket one loop turn after `close()`; a test that ends right
    after closing a peer would otherwise leave that to the garbage collector (ResourceWarning)."""
    yield
    for _ in range(5):
        await asyncio.sleep(0.02)
    # aioice and aiortc leave a few sockets/tasks for the collector; collect them here, inside
    # this test, so a warning about them never lands in a later, unrelated test.
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        gc.collect()
