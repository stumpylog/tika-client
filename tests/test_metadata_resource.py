from datetime import datetime
from datetime import timezone

import magic
from pytest_httpx import HTTPXMock

from tests.config import SAMPLE_DIR
from tests.config import TIKA_URL
from tika_rest_client.client import TikaClient
from tika_rest_client.errors import RestHttpError


class TestMetadataResource:
    def test_metadata_from_docx(self, tika_client):
        test_file = SAMPLE_DIR / "sample.docx"
        resp = tika_client.metadata.from_file(test_file, magic.from_file(str(test_file), mime=True))

        self.assertEqual(resp.type, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        self.assertIsNone(resp.created)

    def test_metadata_from_docx_no_mime(self, tika_client):
        test_file = SAMPLE_DIR / "sample.docx"
        resp = tika_client.metadata.from_file(test_file)

        self.assertEqual(resp.type, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        self.assertIsNone(resp.created)

    def test_metadata_from_word_docx(self, tika_client):
        test_file = SAMPLE_DIR / "microsoft-sample.docx"
        resp = tika_client.metadata.from_file(test_file, magic.from_file(str(test_file), mime=True))

        self.assertEqual(resp.type, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        self.assertEqual(resp.created, datetime(year=2023, month=5, day=17, hour=16, minute=41, tzinfo=timezone.utc))
        self.assertEqual(resp.modified, datetime(year=2023, month=5, day=17, hour=16, minute=44, tzinfo=timezone.utc))

    def test_metadata_from_odt(self, tika_client):
        test_file = SAMPLE_DIR / "sample.odt"
        resp = tika_client.metadata.from_file(test_file, magic.from_file(str(test_file), mime=True))

        self.assertEqual(resp.type, "application/vnd.oasis.opendocument.text")
        self.assertEqual(resp.data["generator"], "LibreOfficeDev/6.0.5.2$Linux_X86_64 LibreOffice_project/")
        self.assertIsNone(resp.created)

    def test_http_error(self, httpx_mock: HTTPXMock):
        httpx_mock.add_response(status_code=500)
        with self.assertRaises(RestHttpError), TikaClient(base_url=TIKA_URL) as client:
            test_file = SAMPLE_DIR / "sample.odt"
            client.metadata.from_file(test_file)
