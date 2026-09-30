# SPDX-FileCopyrightText: 2023-present Trenton H <rda0128ou@mozmail.com>
#
# SPDX-License-Identifier: MPL-2.0

"""Chunked file iterators shared by the httpx-family backends (httpx and httpx2)."""

from __future__ import annotations

from typing import IO
from typing import TYPE_CHECKING

from anyio.to_thread import run_sync

if TYPE_CHECKING:
    from collections.abc import AsyncIterator
    from collections.abc import Iterator

# httpx will not take an open file as a request body: the sync client hangs on one and the
# async client rejects it outright. Both accept an iterator of chunks, which is how a file is
# streamed without being read into memory.
STREAM_CHUNK_SIZE = 64 * 1024


def iter_file(body: IO[bytes]) -> Iterator[bytes]:
    """Yield the file in chunks for a sync client."""
    while chunk := body.read(STREAM_CHUNK_SIZE):
        yield chunk


async def aiter_file(body: IO[bytes]) -> AsyncIterator[bytes]:
    """Yield the file in chunks for an async client, reading off the event loop."""
    while chunk := await run_sync(body.read, STREAM_CHUNK_SIZE):
        yield chunk
