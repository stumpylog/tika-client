# Tika Rest Client

[![PyPI - Version](https://img.shields.io/pypi/v/tika-client.svg)](https://pypi.org/project/tika-client)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/tika-client.svg)](https://pypi.org/project/tika-client)

---

**Table of Contents**

- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [License](#license)

## Features

- Simplified: No need to worry about XML or JSON responses, downloading a Tika jar file or Python 2 leftovers
- Support for Tika 2+ only
- Based on the modern httpx library for support of all modern features
- Full support for type hinting
- Full test coverage run against an actual Tika server for multiple Python and PyPy versions

## Installation

```console
pip install tika-client
```

## Usage

```python3
from pathlib import Path
from tika_client import TikaClient

test_file = Path("sample.docx")

with TikaClient("http://localhost:9998) as client
    metadata = client.metadata.from_file(test_file)

```

## Why

Only one other library for interfacing with Tika exists that I know of. I find it too complicated, trying to handle
too many use cases.

The biggest issue I have with the library is its downloading and running of a jar file
if needed. To me, an API client should only interface to the API and not try to provide functionallity to start
the API as well.

The library also provides a lot of knobs to turn, but I argue most developers will not want to configure XML as
the response type, they just want the data, already parsed.

This library attempts to provide a simpler interface, minimal lines of code and typing of the parsed response.

## License

`tika-client` is distributed under the terms of the [GPL-3.0-only](https://spdx.org/licenses/GPL-3.0-only.html) license.
