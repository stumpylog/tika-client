from __future__ import annotations

import sys
from typing import Optional
from typing import Union

if sys.version_info >= (3, 11):  # pragma: no cover
    from typing import Self
else:  # pragma: no cover
    from typing_extensions import Self  # noqa: F401

MimeType = Optional[str]

RequestContent = Union[str, bytes]
