# tika-client

[![PyPI - Version](https://img.shields.io/pypi/v/tika-client.svg)](https://pypi.org/project/tika-client)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/tika-client.svg)](https://pypi.org/project/tika-client)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/tika-client.svg)](https://pypi.org/project/tika-client)
[![codecov](https://codecov.io/github/stumpylog/tika-client/branch/main/graph/badge.svg?token=PTESS6YUK5)](https://codecov.io/github/stumpylog/tika-client)

A simple, fully-typed Python client for extracting text, HTML, and metadata from documents via the Apache Tika server REST API.

---

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Tika Server Compatibility](#tika-server-compatibility)
- [Usage](#usage)
- [Response Data](#response-data)
  - [Parse failures](#parse-failures)
  - [Truncated parses](#truncated-parses)
- [HTTP Backend Selection](#http-backend-selection)
- [Configuration](#configuration)
- [Why](#why)
- [License](#license)

## Features

- Synchronous and asynchronous client support
- Pluggable HTTP backend (httpx, niquests, or requests)
- `metadata.from_file()` and `rmeta.*.from_file()` stream files to the server via HTTP multipart/form-data (no full file reads into memory). `tika.as_html.from_file()`/`tika.as_text.from_file()` read the file into memory before sending it, as Tika 4 removed the `/tika/form*` routes those relied on.
- Full type annotations with typed response properties
- Supports Tika Server 4.0+ only (the last release supporting Tika 3.x is 1.0.0)
- Tested against a real Tika server across multiple Python and PyPy versions
- Optional gzip response compression

## Installation

No HTTP backend is installed by default. Install `tika-client` with one of the three backend extras:

```console
pip install "tika-client[httpx]"
pip install "tika-client[niquests]"
pip install "tika-client[requests]"
```

All three extras can be combined. The default `backend="auto"` discovers whichever backend is present
at runtime, trying `httpx` first, then `niquests`, then `requests`. A bare `pip install tika-client`
with no extras will raise `ImportError` on first use.

## Tika Server Compatibility

This version requires **Tika Server 4.0 or later**. Tika 4.x is a wire-breaking
release (endpoint paths, metadata key names, and error response formats all
changed). This client does not support Tika Server 3.x. If you need Tika 3.x
support, use `tika-client` 1.0.0, the last release compatible with it.

This version requires **Python 3.11 or later**. Python 3.10 reaches end of life in October 2026,
and this release uses `ExceptionGroup`, which is a 3.11 builtin.

## Usage

All examples use `http://localhost:9998` as the Tika server URL. Replace this with your own server address.

### Metadata Extraction

Extract metadata from a file:

```python
from pathlib import Path
from tika_client import TikaClient

with TikaClient("http://localhost:9998") as client:
    metadata = client.metadata.from_file(Path("sample.docx"))
    print(metadata.title)
    print(metadata.created)
```

```python
from pathlib import Path
from tika_client import AsyncTikaClient

async with AsyncTikaClient("http://localhost:9998") as client:
    metadata = await client.metadata.from_file(Path("sample.docx"))
    print(metadata.title)
    print(metadata.created)
```

### Content Extraction as Plain Text

Extract content as plain text from a file or a buffer:

```python
from pathlib import Path
from tika_client import TikaClient

with TikaClient("http://localhost:9998") as client:
    # From a file
    result = client.tika.as_text.from_file(Path("sample.pdf"))
    print(result.content)

    # From a buffer
    data = Path("sample.pdf").read_bytes()
    result = client.tika.as_text.from_buffer(data, "application/pdf")
    print(result.content)
```

```python
from pathlib import Path
from tika_client import AsyncTikaClient

async with AsyncTikaClient("http://localhost:9998") as client:
    result = await client.tika.as_text.from_file(Path("sample.pdf"))
    print(result.content)

    data = Path("sample.pdf").read_bytes()
    result = await client.tika.as_text.from_buffer(data, "application/pdf")
    print(result.content)
```

### Content Extraction as HTML

Extract content formatted as HTML:

```python
from pathlib import Path
from tika_client import TikaClient

with TikaClient("http://localhost:9998") as client:
    result = client.tika.as_html.from_file(Path("sample.docx"))
    print(result.content)

    data = Path("sample.docx").read_bytes()
    result = client.tika.as_html.from_buffer(data)
    print(result.content)
```

```python
from pathlib import Path
from tika_client import AsyncTikaClient

async with AsyncTikaClient("http://localhost:9998") as client:
    result = await client.tika.as_html.from_file(Path("sample.docx"))
    print(result.content)

    data = Path("sample.docx").read_bytes()
    result = await client.tika.as_html.from_buffer(data)
    print(result.content)
```

### Recursive Metadata

Extract metadata and content from all embedded documents (attachments, embedded files):

```python
from pathlib import Path
from tika_client import TikaClient

with TikaClient("http://localhost:9998") as client:
    # Returns a list, one entry per embedded document
    results = client.rmeta.as_text.from_file(Path("sample.docx"))
    for item in results:
        print(item.content)

    results = client.rmeta.as_html.from_file(Path("sample.docx"))
    for item in results:
        print(item.content)
```

```python
from pathlib import Path
from tika_client import AsyncTikaClient

async with AsyncTikaClient("http://localhost:9998") as client:
    results = await client.rmeta.as_text.from_file(Path("sample.docx"))
    for item in results:
        print(item.content)
```

The MIME type can be provided to all methods as a detection hint:

```python
result = client.tika.as_text.from_file(
    Path("sample.docx"),
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
)
```

Currently, the metadata, tika, and recursive metadata endpoints are implemented. If you need
support for additional Tika endpoints, please open an idea in
[GitHub Discussions](https://github.com/stumpylog/tika-client/discussions/categories/ideas).

> **Note**
> In Tika 4 this is a hint, not an override. Tika 3.x treated a request `Content-Type` as
> authoritative and forced the type; Tika 4 keeps it only when it matches or specializes the
> type detected from the content, and otherwise ignores it (TIKA-4825). Forcing an unrelated
> type onto arbitrary bytes no longer works.

## Response Data

All methods return a `TikaResponse`, except `rmeta.*`, which returns a `TikaResponseList` (a
`list` of `TikaResponse`, one per embedded document). Commonly used typed properties:

```python
result = client.tika.as_text.from_file(Path("sample.pdf"))

result.content          # str | None - extracted text or HTML
result.type             # str - detected MIME type
result.parsers          # list[str] - Tika parsers used
result.content_length   # int | None
result.title            # str | None
result.created          # datetime | None (timezone-aware)
result.modified         # datetime | None (timezone-aware)
result.xmp_created      # datetime | None (timezone-aware)
result.page_count       # int | None
result.character_count  # int | None
result.revision         # int | None
result.last_author      # str | None

result.parse_exception  # str | None - see "Parse failures" below
result.truncated        # bool - the parse hit its deadline and content is incomplete
```

Tika returns many additional fields depending on the file type. The complete parsed JSON response
is always available via `result.data`. The `TikaKey`, `DublinCoreKey`, and `XmpKey` enums provide
typed constants for accessing common keys in `result.data`:

```python
from tika_client import TikaKey, DublinCoreKey, XmpKey

print(result.data[DublinCoreKey.Creator])
print(result.data[TikaKey.Parse_Time])
```

`HttpStatusError` is raised for 4xx and 5xx responses from the Tika server:

```python
from tika_client import TikaClient, HttpStatusError

with TikaClient("http://localhost:9998") as client:
    try:
        result = client.tika.as_text.from_file(Path("sample.pdf"))
    except HttpStatusError as e:
        print(f"Tika returned an error: {e}")
```

### Typed Tika server errors

For a non-2xx response, `tika-client` raises one of the following `TikaServerError` subclasses
instead of a bare `HttpStatusError`:

- `TikaTimeoutError` - a 503 response where the forked Tika worker exceeded its configured
  processing timeout.
- `TikaCrashError` - a 503 (or 500) response where the forked Tika JVM crashed, e.g. from an
  out-of-memory condition.
- `TikaSaturatedError` - a 429 response indicating the server's fork pool is saturated;
  `retry_after` may carry a backoff hint.
- `TikaPayloadTooLargeError` - a 413 response, either because the request body exceeded the
  server's configured size limit or because the parse result exceeded the IPC payload limit.
- `TikaBadRequestError` - a 400 response: the request is malformed, an unknown fetcher or
  emitter was named, or the handler in the path was not recognized. Retrying never helps.
- `TikaPartialParseError` - a 422 response from one of Tika's raw endpoints. This client does
  not call those, so it is not expected in practice; it is kept for defence in depth.
- `TikaServerError` - the base class, also raised directly as a fallback for any other non-2xx
  response that doesn't match one of the more specific cases above.

All of these subclass `HttpStatusError`, which in turn subclasses `TikaError`, the root of every
error this library raises. Any existing `except HttpStatusError` handling continues to work
unchanged. Each instance also carries:

- `tika_status` - the raw `status` value from Tika's JSON error envelope, when the body was
  parseable JSON in that shape (`None` otherwise).
- `message` - the raw `message` value from that same envelope, when present.
- `retry_after` - the `Retry-After` response header parsed as a number of seconds, when present.
- `response_text` - the raw, unparsed response body.

```python
from tika_client import TikaClient, TikaServerError

with TikaClient("http://localhost:9998") as client:
    try:
        result = client.tika.as_text.from_file(Path("sample.pdf"))
    except TikaServerError as e:
        print(f"Tika server error: {e.tika_status} - {e.message}")
```

These cover non-2xx responses only. Tika 4 also reports parse failures on a `200`, which are a
separate family described next.

### Parse failures

Tika 3.x returned a 500 when the container parser failed. **Tika 4 returns a 200** with the
stack trace in `tk:exception:container-exception` and no content at all, so a failed parse would
otherwise be indistinguishable from an empty document.

Two error types describe these, both subclassing `TikaParseError` and so also `TikaError`:

- `TikaContainerParseError` - the container parser failed, so nothing was extracted.
- `TikaEmbeddedParseError` - an embedded document failed while its container parsed fine. Only
  reachable from `rmeta.*`, and never raised automatically, since the surrounding documents
  succeeded.

Both carry `detail`, the server-side message, which is usually a Java stack trace.

For `tika.*` and `metadata.*`, which describe a single document, the failure is total and is
raised:

```python
from tika_client import TikaClient, TikaContainerParseError

with TikaClient("http://localhost:9998") as client:
    try:
        result = client.tika.as_text.from_file(Path("corrupt.docx"))
    except TikaContainerParseError as e:
        print(f"Tika could not parse the document: {e}")
```

For `rmeta.*`, which returns one entry per embedded document, raising would throw away the
entries that parsed successfully, so failures are exposed instead:

```python
results = client.rmeta.as_text.from_file(Path("archive-with-a-bad-attachment.docx"))

if results.has_parse_errors:
    for entry in results:
        if entry.parse_exception is not None:
            print(f"failed: {entry.parse_exception}")

# Or raise on demand, the way httpx defers raise_for_status() to you.
# The list form raises a TikaParseErrorGroup, so every failure is reported, not just the first.
results.raise_for_parse_status()

# The same method exists on an individual response, raising the one matching error.
results[0].raise_for_parse_status()
```

`raise_for_parse_status()` is available on both `TikaResponse` and `TikaResponseList`. The
single-response form raises `TikaContainerParseError` or `TikaEmbeddedParseError` directly; the
list form always raises a `TikaParseErrorGroup`, even for a single failure, so that handling does
not depend on how many documents happened to fail. Neither raises for truncation.

`TikaParseErrorGroup` is an `ExceptionGroup`, so `except*` works, and it is also a `TikaError`:

```python
try:
    results.raise_for_parse_status()
except* TikaEmbeddedParseError as eg:
    for err in eg.exceptions:
        print(err.detail)
```

### Truncated parses

Tika 4 adds `PARTIAL_TIMEOUT`: a parse that exceeds its deadline returns a 200 with whatever
content was extracted so far. This is **not** raised, because that content is real and usable,
and it is deliberately not part of `has_parse_errors`, because truncation is not a parse failure.
Check it explicitly when an incomplete document matters:

```python
result = client.tika.as_text.from_file(Path("enormous.pdf"))

if result.truncated:
    print("Tika hit its deadline; this content is incomplete")
```

The server-side default is generous (`totalTaskTimeoutMillis` is an hour), so this is uncommon,
but it is silent if you do not look for it.

## HTTP Backend Selection

No backend is installed by default. Install at least one extra and select it explicitly, or let
`"auto"` (the default) detect whichever is present (tries `httpx`, then `niquests`, then `requests`):

```python
from tika_client import TikaClient

# Auto-detect: prefers httpx, then niquests, then requests (default)
with TikaClient("http://localhost:9998") as client: ...

# Explicit httpx
with TikaClient("http://localhost:9998", backend="httpx") as client: ...

# Explicit niquests
with TikaClient("http://localhost:9998", backend="niquests") as client: ...

# Explicit requests (sync only)
with TikaClient("http://localhost:9998", backend="requests") as client: ...
```

The same `backend` parameter is available on `AsyncTikaClient`. Note that the `requests` backend
does not support async and will raise a `ValueError` if used with `AsyncTikaClient`.

## Configuration

All constructor parameters for both `TikaClient` and `AsyncTikaClient`:

| Parameter    | Default                 | Description                                                      |
| ------------ | ----------------------- | ---------------------------------------------------------------- |
| `tika_url`   | (required)              | URL of the Tika server                                           |
| `timeout`    | `30.0`                  | Request timeout in seconds                                       |
| `compress`   | `False`                 | Request gzip-compressed responses from the server                |
| `user_agent` | `tika-client/{version}` | Value sent as the User-Agent header                              |
| `log_level`  | `logging.ERROR`         | Log level for the HTTP backend logger                            |
| `backend`    | `"auto"`                | HTTP backend: `"httpx"`, `"niquests"`, `"requests"`, or `"auto"` |

## Why

The primary alternative is [tika-python](https://github.com/chrismattmann/tika-python), which is
a capable library with a long history. If it works well for your use case, it is a fine choice.

`tika-client` takes a different philosophy:

**No Java required at runtime.** `tika-python` can download and start the Tika JAR automatically,
which requires Java to be installed. `tika-client` is a pure REST client. You bring your own
Tika server (a single Docker image does the job), and the library only talks to it over HTTP.

**Typed responses, not raw dicts.** `tika-python` returns plain Python dicts. `tika-client`
parses the response into a typed `TikaResponse` object with `datetime`, `int`, and `str` fields
where the type is known, so your editor and type checker can help you.

**Async support.** `tika-client` provides `AsyncTikaClient` alongside the synchronous client,
making it straightforward to use in async applications.

**Minimal surface area.** `tika-python` exposes language detection, translation, and
configuration inspection endpoints. `tika-client` focuses on what most developers actually use:
extracting text, HTML, and metadata from documents.

## License

`tika-client` is distributed under the terms of the [Mozilla Public License 2.0](https://spdx.org/licenses/MPL-2.0.html) license.
