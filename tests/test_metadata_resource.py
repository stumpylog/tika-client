from datetime import datetime
from datetime import timezone

import magic
import pytest
from pytest_httpx import HTTPXMock

from tests.config import SAMPLE_DIR
from tests.config import TIKA_URL
from tika_rest_client.client import TikaClient
from tika_rest_client.errors import RestHttpError


class TestMetadataResource:
    def test_metadata_from_docx(self, tika_client):
        test_file = SAMPLE_DIR / "sample.docx"
        resp = tika_client.metadata.from_file(test_file, magic.from_file(str(test_file), mime=True))

        assert resp.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        assert resp.created is None

    def test_metadata_from_docx_no_mime(self, tika_client):
        test_file = SAMPLE_DIR / "sample.docx"
        resp = tika_client.metadata.from_file(test_file)

        assert resp.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        assert resp.created is None

    def test_metadata_from_word_docx(self, tika_client):
        test_file = SAMPLE_DIR / "microsoft-sample.docx"
        resp = tika_client.metadata.from_file(test_file, magic.from_file(str(test_file), mime=True))

        assert resp.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        assert resp.created == datetime(year=2023, month=5, day=17, hour=16, minute=41, tzinfo=timezone.utc)
        assert resp.modified == datetime(year=2023, month=5, day=17, hour=16, minute=44, tzinfo=timezone.utc)

    def test_metadata_from_odt(self, tika_client):
        test_file = SAMPLE_DIR / "sample.odt"
        resp = tika_client.metadata.from_file(test_file, magic.from_file(str(test_file), mime=True))

        assert resp.type == "application/vnd.oasis.opendocument.text"
        assert resp.data["generator"] == "LibreOfficeDev/6.0.5.2$Linux_X86_64 LibreOffice_project/"
        assert resp.created is None

    def test_http_error(self, httpx_mock: HTTPXMock):
        test_file = SAMPLE_DIR / "sample.odt"

        httpx_mock.add_response(status_code=500)
        with pytest.raises(RestHttpError), TikaClient(base_url=TIKA_URL) as client:
            client.metadata.from_file(test_file)
