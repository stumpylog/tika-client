# SPDX-FileCopyrightText: 2023-present Trenton H <rda0128ou@mozmail.com>
#
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import re
from abc import ABC
from abc import abstractmethod
from mimetypes import guess_type
from typing import IO
from typing import TYPE_CHECKING
from typing import Any
from typing import Generic
from typing import Literal
from typing import TypeVar
from urllib.parse import quote

from anyio import Path as AsyncPath
from anyio.to_thread import run_sync

from tika_client._constants import MIN_COMPRESS_LEN
from tika_client._http_backends._protocols import AsyncClientProtocol
from tika_client._http_backends._protocols import SyncClientProtocol
from tika_client.data_models import TikaKey
from tika_client.data_models import TikaResponse
from tika_client.exceptions import HttpStatusError
from tika_client.exceptions import TikaContainerParseError
from tika_client.exceptions import TikaEmbeddedParseError
from tika_client.exceptions import raise_for_tika_status

if TYPE_CHECKING:
    from collections.abc import Coroutine
    from pathlib import Path


T = TypeVar("T", bound="SyncClientProtocol | AsyncClientProtocol")

# Which in-band parse failures raise, which differs by what the endpoint returns.
ParseErrorMode = Literal["all", "container", "none"]

# Matches C0 control characters (including CR/LF) and DEL, none of which are
# valid in an HTTP header value. httpx/niquests/requests all reject these at
# send time with an opaque, backend-specific error; raising here fails fast
# with a clear message instead.
_CONTROL_CHAR_RE = re.compile(r"[\x00-\x1f\x7f]")


def _open_binary(path: Path) -> IO[bytes]:
    """Open a file for binary reading, as a named function so the mode stays visible to typing."""
    return path.open("rb")


class BaseResource(ABC, Generic[T]):
    def __init__(self, client: T, *, compress: bool) -> None:
        self.client = client
        self.compress = compress

    @staticmethod
    def get_content_headers(filename: str, disposition: str = "attachment") -> dict[str, str]:
        """
        Given a filename, returns the attachment header.

        Args:
            filename: The filename to encode
            disposition: The disposition of the file, defaults to attachment

        Returns:
            The attachment header

        Raises:
            ValueError: If filename contains a control character, which is not valid in an
                HTTP header value.

        """
        if _CONTROL_CHAR_RE.search(filename):
            msg = f"Filename {filename!r} contains a control character and cannot be used in a header value"
            raise ValueError(msg)

        try:
            # Test if filename is ASCII
            filename.encode("ascii")
        except UnicodeEncodeError:
            # For non-ASCII, provide ASCII fallback and UTF-8 encoded version
            ascii_filename = filename.encode("ascii", "replace").decode("ascii")
            # Replace ? marks from replace encoding with underscore for better readability
            ascii_filename = ascii_filename.replace("?", "_")
            # Escape quotes in ASCII version
            ascii_filename = ascii_filename.replace('"', '\\"')
            # UTF-8 encode the original filename and percent-encode the bytes
            utf8_filename = quote(filename.encode("utf-8"))

            return {
                "Content-Disposition": f'{disposition}; filename="{ascii_filename}"; '
                f"filename*=UTF-8''{utf8_filename}",
            }
        else:
            # If ASCII, we still need to escape quotes
            escaped_filename = filename.replace('"', '\\"')
            return {
                "Content-Disposition": f'{disposition}; filename="{escaped_filename}"',
            }

    @abstractmethod
    def put_multipart(  # pragma: no cover
        self,
        endpoint: str,
        filepath: Path,
        mime_type: str | None = None,
    ) -> Any | Coroutine[Any, Any, Any]:  # noqa: ANN401
        """
        Given an endpoint, file and a mime type, does a multi-part form data upload of the file to the end point.

        Returns the JSON response of the server

        Args:
            endpoint: The endpoint to send the file to
            filepath: The path to the file to send
            mime_type: The mime type of the file to send, if it's not provided, it will be guessed

        Returns:
            The JSON response of the server

        """

    @abstractmethod
    def put_content(  # pragma: no cover
        self,
        endpoint: str,
        content: str | bytes,
        mime_type: str | None = None,
        filename: str | None = None,
    ) -> Any | Coroutine[Any, Any, Any]:  # noqa: ANN401
        """
        Give, an endpoint, content and optional mime type, does an HTTP PUT with the given content.

        Returns the JSON response of the server

        Args:
            endpoint: The endpoint to send the content to
            content: The content to send
            mime_type: The mime type of the content, if it's not provided, it will be guessed
            filename: If provided, sent as a Content-Disposition filename hint

        Returns:
            The JSON response of the server

        """

    def _prepare_content(
        self,
        content: str | bytes,
        mime_type: str | None,
        filename: str | None,
        *,
        compress_body: bool = True,
    ) -> tuple[bytes, dict[str, str]]:
        """
        Encode the body and build its headers, compressing when that is enabled and worthwhile.

        compress_body is False for the async caller, which compresses in a worker thread and
        folds the result back in rather than blocking the event loop.
        """
        content_bytes = content.encode() if isinstance(content, str) else content
        content_length = len(content_bytes)

        headers = dict(BaseResource.get_content_headers(filename)) if filename is not None else {}
        if compress_body and self.compress and content_length > MIN_COMPRESS_LEN:
            from gzip import compress  # noqa: PLC0415

            content_bytes = compress(content_bytes)
            content_length = len(content_bytes)
            headers["Content-Encoding"] = "gzip"

        headers["Content-Length"] = str(content_length)
        if mime_type is not None:
            headers["Content-Type"] = mime_type
        return content_bytes, headers

    @staticmethod
    def decoded_response(resp_json: dict[str, Any], *, on_parse_error: ParseErrorMode = "all") -> TikaResponse:
        """
        Return the decoded JSON from Tika with helpers for access.

        Args:
            resp_json: The JSON response from the server
            on_parse_error: Which in-band parse failures should raise. "all" for the
                single-document content endpoints, where a failure means content the caller
                asked for is missing. "container" for /meta, which returns container metadata
                only, so an embedded failure does not affect its answer. "none" for /rmeta,
                where raising would discard the entries that did parse.

        Returns:
            The decoded response

        Raises:
            TikaContainerParseError: The container parser failed, so nothing was extracted.
            TikaEmbeddedParseError: An embedded document failed while its container parsed.
                Tika reports both on an HTTP 200, so they have to be detected here.

        """
        if on_parse_error != "none":
            # Container first: a failed container makes the embedded failure moot. Checked on
            # the raw payload rather than a constructed TikaResponse, so a failure response
            # missing an otherwise-required key still raises the right error.
            container = resp_json.get(TikaKey.ContainerException)
            if container is not None:
                raise TikaContainerParseError(data=resp_json, detail=container)
            embedded = resp_json.get(TikaKey.EmbeddedException)
            if embedded is not None and on_parse_error == "all":
                raise TikaEmbeddedParseError(data=resp_json, detail=embedded)
        return TikaResponse(resp_json)


class SyncResource(BaseResource[SyncClientProtocol]):
    def put_multipart(
        self,
        endpoint: str,
        filepath: Path,
        mime_type: str | None = None,
    ) -> Any:  # noqa: ANN401
        """
        Given an endpoint, file and a mime type, does a multi-part form data upload of the file to the end point.

        Args:
            endpoint: The endpoint to send the file to
            filepath: The path to the file to send
            mime_type: The mime type of the file to send, if it's not provided, it will be guessed

        Returns:
            Returns the JSON response of the server

        """
        with filepath.open("rb") as handler:
            response = self.client.post(
                endpoint,
                files={
                    "upload-file": (
                        filepath.name,
                        handler,
                        mime_type or guess_type(filepath.name)[0] or "",
                    ),
                },
                headers=BaseResource.get_content_headers(filepath.name),
            )
        try:
            response.raise_for_status()
        except HttpStatusError as e:
            raise_for_tika_status(response, cause=e)
        return response.json()

    def put_content(
        self,
        endpoint: str,
        content: str | bytes,
        mime_type: str | None = None,
        filename: str | None = None,
    ) -> Any:  # noqa: ANN401
        """
        Give, an endpoint, content and optional mime type, does an HTTP PUT with the given content.

        Args:
            endpoint: The endpoint to send the content to
            content: The content to send
            mime_type: The mime type of the content, if it's not provided, it will be guessed
            filename: If provided, sent as a Content-Disposition filename hint

        Returns:
            Returns the JSON response of the server

        """
        content_bytes, headers = self._prepare_content(content, mime_type, filename)

        response = self.client.put(endpoint, content=content_bytes, headers=headers)
        try:
            response.raise_for_status()
        except HttpStatusError as e:
            raise_for_tika_status(response, cause=e)
        return response.json()

    def put_file(
        self,
        endpoint: str,
        filepath: Path,
        mime_type: str | None = None,
    ) -> Any:  # noqa: ANN401
        """
        PUT a file to an endpoint without reading it into memory.

        Content-Length comes from stat() rather than from the buffer, which is what lets the
        body stream. Compression is the exception: the compressed length is not knowable
        without compressing, so that path still buffers.

        filepath must be a regular file. A FIFO or character device reports st_size == 0 and
        then yields bytes, which fails loudly rather than corrupting: httpx raises
        h11.LocalProtocolError for the length mismatch, and the other backends recompute the
        length from the handle.

        Args:
            endpoint: The endpoint to send the file to
            filepath: The path of the file to send
            mime_type: The mime type of the file, guessed from the name if not provided

        Returns:
            The JSON response of the server

        """
        size = filepath.stat().st_size
        # An empty body must go through put_content. requests and niquests compute the length
        # from the handle, and super_len() == 0 is falsy, so they add Transfer-Encoding: chunked
        # alongside our Content-Length: 0. Jetty rejects that combination with a 400.
        if self.compress or size == 0:
            return self.put_content(endpoint, filepath.read_bytes(), mime_type, filepath.name)

        headers = dict(BaseResource.get_content_headers(filepath.name))
        headers["Content-Length"] = str(size)
        # Set only when given, exactly as put_content does. Guessing here would volunteer a
        # confidently wrong type for a misnamed file, where sending nothing lets Tika detect.
        if mime_type is not None:
            headers["Content-Type"] = mime_type

        with filepath.open("rb") as handle:
            response = self.client.put(endpoint, content=handle, headers=headers)
        try:
            response.raise_for_status()
        except HttpStatusError as e:
            raise_for_tika_status(response, cause=e)
        return response.json()


class AsyncResource(BaseResource[AsyncClientProtocol]):
    async def put_multipart(
        self,
        endpoint: str,
        filepath: Path,
        mime_type: str | None = None,
    ) -> Any:  # noqa: ANN401
        """
        Given an endpoint, file and a mime type, does a multi-part form data upload of the file to the end point.

        Args:
            endpoint: The endpoint to send the file to
            filepath: The path to the file to send
            mime_type: The mime type of the file to send, if it's not provided, it will be guessed

        Returns:
            Returns the JSON response of the server

        """
        with filepath.open("rb") as handler:
            response = await self.client.post(
                endpoint,
                files={
                    "upload-file": (
                        filepath.name,
                        handler,
                        mime_type or guess_type(filepath.name)[0] or "",
                    ),
                },
                headers=self.get_content_headers(filepath.name),
            )
        try:
            response.raise_for_status()
        except HttpStatusError as e:
            raise_for_tika_status(response, cause=e)
        return response.json()

    async def put_content(
        self,
        endpoint: str,
        content: str | bytes,
        mime_type: str | None = None,
        filename: str | None = None,
    ) -> Any:  # noqa: ANN401
        """
        Give, an endpoint, content and optional mime type, does an HTTP PUT with the given content.

        Args:
            endpoint: The endpoint to send the content to
            content: The content to send
            mime_type: The mime type of the content, if it's not provided, it will be guessed
            filename: If provided, sent as a Content-Disposition filename hint

        Returns:
            Returns the JSON response of the server

        """
        # Compression runs in a thread here, so the shared helper is told not to do it and the
        # result is folded back in. Keeps one implementation of the header logic.
        content_bytes, headers = self._prepare_content(content, mime_type, filename, compress_body=False)
        if self.compress and len(content_bytes) > MIN_COMPRESS_LEN:
            from gzip import compress  # noqa: PLC0415

            content_bytes = await run_sync(compress, content_bytes)
            headers["Content-Encoding"] = "gzip"
            headers["Content-Length"] = str(len(content_bytes))

        response = await self.client.put(endpoint, content=content_bytes, headers=headers)
        try:
            response.raise_for_status()
        except HttpStatusError as e:
            raise_for_tika_status(response, cause=e)
        return response.json()

    async def put_file(
        self,
        endpoint: str,
        filepath: Path,
        mime_type: str | None = None,
    ) -> Any:  # noqa: ANN401
        """
        PUT a file to an endpoint without reading it into memory.

        Content-Length comes from stat() rather than from the buffer, which is what lets the
        body stream. Compression is the exception: the compressed length is not knowable
        without compressing, so that path still buffers.

        filepath must be a regular file. A FIFO or character device reports st_size == 0 and
        then yields bytes, which fails loudly rather than corrupting: httpx raises
        h11.LocalProtocolError for the length mismatch, and the other backends recompute the
        length from the handle.

        Args:
            endpoint: The endpoint to send the file to
            filepath: The path of the file to send
            mime_type: The mime type of the file, guessed from the name if not provided

        Returns:
            The JSON response of the server

        """
        size = (await AsyncPath(filepath).stat()).st_size
        # See the sync twin: an empty body would collide Content-Length with the chunked
        # encoding requests and niquests add for a zero-length handle.
        if self.compress or size == 0:
            return await self.put_content(endpoint, await run_sync(filepath.read_bytes), mime_type, filepath.name)

        headers = dict(BaseResource.get_content_headers(filepath.name))
        # open and close stay on worker threads: the handle must remain a plain sync file,
        # because the niquests async adapter passes it straight to the request. The httpx adapter
        # reads its chunks off the loop too; the niquests adapter reads them inline, since it
        # takes the handle directly.
        headers["Content-Length"] = str(size)
        if mime_type is not None:
            headers["Content-Type"] = mime_type

        handle = await run_sync(_open_binary, filepath)
        try:
            response = await self.client.put(endpoint, content=handle, headers=headers)
        finally:
            await run_sync(handle.close)
        try:
            response.raise_for_status()
        except HttpStatusError as e:
            raise_for_tika_status(response, cause=e)
        return response.json()
