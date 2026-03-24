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
- [Usage](#usage)
- [Response Data](#response-data)
- [HTTP Backend Selection](#http-backend-selection)
- [Configuration](#configuration)
- [Why](#why)
- [License](#license)

## Features

- Synchronous and asynchronous client support
- Pluggable HTTP backend (httpx, niquests, or requests)
- Uses HTTP multipart/form-data to stream files to the server (no full file reads into memory)
- Full type annotations with typed response properties
- Support for Tika 2 and Tika 3 (the API did not change between versions)
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

The MIME type can be provided to all methods for more accurate `Content-Type` detection:

```python
result = client.tika.as_text.from_file(
    Path("sample.docx"),
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
)
```

Currently, the metadata, tika, and recursive metadata endpoints are implemented. If you need
support for additional Tika endpoints, please open an idea in
[GitHub Discussions](https://github.com/stumpylog/tika-client/discussions/categories/ideas).

## Response Data

All methods return a `TikaResponse` (or `list[TikaResponse]` for `rmeta`). Commonly used typed properties:

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
result.language         # str | None
result.character_count  # int | None
result.revision         # int | None
result.last_author      # str | None
```

Tika returns many additional fields depending on the file type. The complete parsed JSON response
is always available via `result.data`. The `TikaKey`, `DublinCoreKey`, and `XmpKey` enums provide
typed constants for accessing common keys in `result.data`:

```python
from tika_client import TikaKey, DublinCoreKey, XmpKey

print(result.data[DublinCoreKey.Creator])
print(result.data[TikaKey.ParseTime])
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
