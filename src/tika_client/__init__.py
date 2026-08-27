"""Public interface to the Tika client library."""
# SPDX-FileCopyrightText: 2023-present Trenton H <rda0128ou@mozmail.com>
#
# SPDX-License-Identifier: MPL-2.0

from tika_client._http_backends._protocols import HttpStatusError
from tika_client.client import AsyncTikaClient
from tika_client.client import TikaClient
from tika_client.data_models import DublinCoreKey
from tika_client.data_models import TikaKey
from tika_client.data_models import XmpKey
from tika_client.exceptions import TikaContainerParseError
from tika_client.exceptions import TikaCrashError
from tika_client.exceptions import TikaEmbeddedParseError
from tika_client.exceptions import TikaError
from tika_client.exceptions import TikaParseError
from tika_client.exceptions import TikaPartialParseError
from tika_client.exceptions import TikaPayloadTooLargeError
from tika_client.exceptions import TikaSaturatedError
from tika_client.exceptions import TikaServerError
from tika_client.exceptions import TikaTimeoutError

__all__ = [
    "AsyncTikaClient",
    "DublinCoreKey",
    "HttpStatusError",
    "TikaClient",
    "TikaContainerParseError",
    "TikaCrashError",
    "TikaEmbeddedParseError",
    "TikaError",
    "TikaKey",
    "TikaParseError",
    "TikaPartialParseError",
    "TikaPayloadTooLargeError",
    "TikaSaturatedError",
    "TikaServerError",
    "TikaTimeoutError",
    "XmpKey",
]
