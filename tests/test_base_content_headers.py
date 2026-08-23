"""
Unit tests for BaseResource.get_content_headers.
These do not require Docker or a live Tika server.
"""

import pytest

from tika_client._base import BaseResource


class TestGetContentHeadersValid:
    def test_ascii_filename(self) -> None:
        headers = BaseResource.get_content_headers("document.pdf")

        assert headers == {"Content-Disposition": 'attachment; filename="document.pdf"'}

    def test_ascii_filename_with_quotes(self) -> None:
        headers = BaseResource.get_content_headers('a "quoted" file.pdf')

        assert headers == {"Content-Disposition": 'attachment; filename="a \\"quoted\\" file.pdf"'}

    def test_non_ascii_filename(self) -> None:
        headers = BaseResource.get_content_headers("Kostenerstattung für Meldebescheinigung.docx")

        assert "Content-Disposition" in headers
        assert "filename*=UTF-8''" in headers["Content-Disposition"]

    def test_custom_disposition(self) -> None:
        headers = BaseResource.get_content_headers("document.pdf", disposition="inline")

        assert headers == {"Content-Disposition": 'inline; filename="document.pdf"'}


class TestGetContentHeadersRejectsControlCharacters:
    def test_embedded_crlf_raises(self) -> None:
        with pytest.raises(ValueError, match="control character"):
            BaseResource.get_content_headers('evil.txt\r\nX-Injected: pwned"')

    def test_embedded_lf_raises(self) -> None:
        with pytest.raises(ValueError, match="control character"):
            BaseResource.get_content_headers("evil\ntest.txt")

    def test_embedded_null_byte_raises(self) -> None:
        with pytest.raises(ValueError, match="control character"):
            BaseResource.get_content_headers("evil\x00test.txt")

    def test_embedded_tab_raises(self) -> None:
        with pytest.raises(ValueError, match="control character"):
            BaseResource.get_content_headers("evil\ttest.txt")

    def test_embedded_del_raises(self) -> None:
        with pytest.raises(ValueError, match="control character"):
            BaseResource.get_content_headers("evil\x7ftest.txt")

    def test_control_character_in_non_ascii_filename_also_raises(self) -> None:
        with pytest.raises(ValueError, match="control character"):
            BaseResource.get_content_headers("Kostenerstattung\r\nfür Meldebescheinigung.docx")
