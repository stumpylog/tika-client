"""
Unit tests for TikaResponse's handling of malformed/incomplete Tika JSON responses.
These do not require Docker or a live Tika server.
"""

from tika_client.data_models import TikaKey
from tika_client.data_models import TikaResponse


class TestTikaResponseMissingParsers:
    def test_missing_parsers_key_defaults_to_empty_list(self) -> None:
        """
        Tika returns a 200 with no tk:parsed-by key when it couldn't parse at all,
        e.g. a zero-byte file, alongside an embedded tk:exception:container-exception.
        """
        data = {
            TikaKey.ContentType: "application/octet-stream",
            "tk:exception:container-exception": "org.apache.tika.exception.ZeroByteFileException: ...",
        }

        resp = TikaResponse(data)

        assert resp.parsers == []
        assert resp.type == "application/octet-stream"
