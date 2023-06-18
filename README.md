# Tika Rest Client

[![PyPI - Version](https://img.shields.io/pypi/v/tika-client.svg)](https://pypi.org/project/tika-client)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/tika-client.svg)](https://pypi.org/project/tika-client)
[![codecov](https://codecov.io/github/stumpylog/tika-client/branch/main/graph/badge.svg?token=PTESS6YUK5)](https://codecov.io/github/stumpylog/tika-client)

---

**Table of Contents**

- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Why](#why)
- [License](#license)

## Features

- Simplified: No need to worry about XML or JSON responses, downloading a Tika jar file or Python 2
- Support for Tika 2+ only
- Based on the modern [httpx](https://github.com/encode/httpx) library
- Full support for type hinting
- Nearly full test coverage run against an actual Tika server for multiple Python and PyPy versions
- Uses HTTP multipart/form-data to stream files to the server (instead of reading into memory)
- Optional compression for parsing from a file content already in a buffer (as opposed to a file)

## Installation

```console
pip3 install tika-client
```

## Usage

```python3
from pathlib import Path
from tika_client import TikaClient

test_file = Path("sample.docx")


with TikaClient("http://localhost:9998) as client

    # Extract a document's metadata
    metadata = client.metadata.from_file(test_file)

    # Get the content of a document as HTML
    data = client.tika.as_html.from_file(test_file)

    # Or as plain text
    text = client.tika.as_text.from_file(test_file)

    # Content and metadata combined
    data = client.rmeta.as_text.from_file(test_file)

    # The mime type can also be given
    # This allows Content-Type to be set most accurately
    text = client.tika.as_text.from_file(test_file,
                                         "application/vnd.openxmlformats-officedocument.wordprocessingml.document")

```

The Tika REST API documentation can be found [here](https://cwiki.apache.org/confluence/display/TIKA/TikaServer).
At the moment, only the metadata, tika and recursive metadata endpoints are implemented.

Unfortunately, the set of possible return values of the Tika API are not very well documented. The library makes
a best effort to extract relevant fields into type properties where it understands more about the mime type
of the document (as returned by Tika). This includes information like created/modified information as time zone
aware `datetime` objects. The full JSON response is always available to the user under the `.data`
attribute.

When a particular key is not present in the response, all properties will return `None` instead.

## Why

Only one other library for interfacing with Tika exists that I know of. I find it too complicated, trying to handle
a lot of differing uses.

The biggest issue I have with the library is its downloading and running of a jar file if needed. To me, an
API client should only interface to the API and not try to provide functionality to start
the API as well. The user is responsible for providing the server with the Tika version they desire.

The library also provides a lot of knobs to turn, but I argue most developers will not want to configure XML as
the response type, they just want the data, already parsed to the maximum extend possible.

This library attempts to provide a simpler interface, minimal lines of code and typing of the parsed response.

## License

`tika-client` is distributed under the terms of the [GPL-3.0-only](https://spdx.org/licenses/GPL-3.0-only.html) license.
