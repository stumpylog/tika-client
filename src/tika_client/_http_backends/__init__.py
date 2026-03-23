# SPDX-FileCopyrightText: 2023-present Trenton H <rda0128ou@mozmail.com>
#
# SPDX-License-Identifier: MPL-2.0

"""Pluggable HTTP backend factory for tika-client."""

from __future__ import annotations

import logging
from typing import Literal

from tika_client._http_backends._protocols import AsyncClientProtocol
from tika_client._http_backends._protocols import HttpStatusError
from tika_client._http_backends._protocols import SyncClientProtocol

BackendType = Literal["httpx", "niquests", "auto"]

__all__ = ["BackendType", "HttpStatusError", "make_async_client", "make_sync_client"]


def _resolve_backend(backend: BackendType) -> Literal["httpx", "niquests"]:
    """Resolve 'auto' to a concrete backend name, preferring httpx."""
    if backend == "auto":
        try:
            import httpx  # noqa: F401, PLC0415
        except ImportError:
            pass
        else:
            return "httpx"
        try:
            import niquests  # noqa: F401, PLC0415
        except ImportError:
            pass
        else:
            return "niquests"
        msg = "No HTTP backend available; install httpx or niquests"
        raise ImportError(msg)
    return backend


def make_sync_client(
    backend: BackendType,
    base_url: str,
    timeout: float,
    headers: dict[str, str],
    log_level: int,
) -> SyncClientProtocol:
    """Create and return a synchronous HTTP client for the given backend."""
    resolved = _resolve_backend(backend)
    if resolved == "httpx":
        import httpx  # noqa: PLC0415

        from tika_client._http_backends._httpx import HttpxSyncAdapter  # noqa: PLC0415

        logging.getLogger("httpx").setLevel(log_level)
        logging.getLogger("httpcore").setLevel(log_level)
        return HttpxSyncAdapter(httpx.Client(base_url=base_url, timeout=timeout, headers=headers))

    import niquests  # noqa: PLC0415

    from tika_client._http_backends._niquests import NiquestsSyncAdapter  # noqa: PLC0415

    logging.getLogger("niquests").setLevel(log_level)
    logging.getLogger("urllib3").setLevel(log_level)
    session = niquests.Session()
    session.headers.update(headers)
    return NiquestsSyncAdapter(session, base_url, timeout)


def make_async_client(
    backend: BackendType,
    base_url: str,
    timeout: float,
    headers: dict[str, str],
    log_level: int,
) -> AsyncClientProtocol:
    """Create and return an asynchronous HTTP client for the given backend."""
    resolved = _resolve_backend(backend)
    if resolved == "httpx":
        import httpx  # noqa: PLC0415

        from tika_client._http_backends._httpx import HttpxAsyncAdapter  # noqa: PLC0415

        logging.getLogger("httpx").setLevel(log_level)
        logging.getLogger("httpcore").setLevel(log_level)
        return HttpxAsyncAdapter(httpx.AsyncClient(base_url=base_url, timeout=timeout, headers=headers))

    import niquests  # noqa: PLC0415

    from tika_client._http_backends._niquests import NiquestsAsyncAdapter  # noqa: PLC0415

    logging.getLogger("niquests").setLevel(log_level)
    logging.getLogger("urllib3").setLevel(log_level)
    session = niquests.AsyncSession()
    session.headers.update(headers)
    return NiquestsAsyncAdapter(session, base_url, timeout)
