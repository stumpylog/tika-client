from datetime import datetime
from datetime import timezone

import httpx
import magic
import pytest
from pytest_httpx import HTTPXMock

from tests.conftest import SAMPLE_DIR
from tests.conftest import TIKA_URL
from tika_client.client import TikaClient


class TestMetadataResource:
    def test_metadata_from_docx(self, tika_client: TikaClient):
        """
        Test parsing of a DOCX produced by Google Docs conversion
        """
        test_file = SAMPLE_DIR / "sample.docx"
        resp = tika_client.metadata.from_file(test_file, magic.from_file(str(test_file), mime=True))

        assert resp.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        assert resp.created is None

    def test_metadata_from_docx_no_mime(self, tika_client: TikaClient):
        """
        Test parsing of a DOCX produced by Google Docs conversion, when no mime type is provided
        """
        test_file = SAMPLE_DIR / "sample.docx"
        resp = tika_client.metadata.from_file(test_file)

        assert resp.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        assert resp.created is None

    def test_metadata_from_word_docx(self, tika_client: TikaClient):
        """
        Test parsing of a DOCX produced by Microsoft Word
        """
        test_file = SAMPLE_DIR / "microsoft-sample.docx"
        resp = tika_client.metadata.from_file(test_file, magic.from_file(str(test_file), mime=True))

        assert resp.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        assert resp.created == datetime(year=2023, month=5, day=17, hour=16, minute=41, tzinfo=timezone.utc)
        assert resp.modified == datetime(year=2023, month=5, day=17, hour=16, minute=44, tzinfo=timezone.utc)

    def test_metadata_from_odt(self, tika_client: TikaClient):
        """
        Test parsing of a ODT produced by Google Docs conversion
        """
        test_file = SAMPLE_DIR / "sample.odt"
        resp = tika_client.metadata.from_file(test_file, magic.from_file(str(test_file), mime=True))

        assert resp.type == "application/vnd.oasis.opendocument.text"
        assert resp.data["generator"] == "LibreOfficeDev/6.0.5.2$Linux_X86_64 LibreOffice_project/"
        assert resp.created is None

    def test_metadata_from_doc(self, tika_client: TikaClient):
        """
        Test parsing of a DOC produced by Google Docs conversion
        """
        test_file = SAMPLE_DIR / "sample.doc"
        resp = tika_client.metadata.from_file(test_file, magic.from_file(str(test_file), mime=True))

        assert resp.type == "application/msword"
        assert resp.language == "en"

    def test_http_error(self, httpx_mock: HTTPXMock):
        """
        Test handling of HTTP errors returned from Tika
        """
        test_file = SAMPLE_DIR / "sample.odt"

        httpx_mock.add_response(status_code=500)
        with pytest.raises(httpx.HTTPStatusError) as err, TikaClient(tika_url=TIKA_URL) as client:
            client.metadata.from_file(test_file)
        assert err.value.response.status_code == httpx.codes.INTERNAL_SERVER_ERROR
