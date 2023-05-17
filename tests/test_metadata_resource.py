from datetime import datetime
from unittest import TestCase

import magic

try:
    from zoneinfo import ZoneInfo
except ImportError:
    from backports.zoneinfo import ZoneInfo

from tests.config import SAMPLE_DIR
from tests.config import TIKA_URL
from tika_rest_client.client import TikaClient


class TestMetadataResource(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TikaClient(base_url=TIKA_URL)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.client.close()
        cls.client = None

    def test_metadata_from_docx(self):
        test_file = SAMPLE_DIR / "sample.docx"
        resp = self.client.metadata.from_file(test_file, magic.from_file(str(test_file), mime=True))

        self.assertEqual(resp.type, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        self.assertIsNone(resp.created)

    def test_metadata_from_word_docx(self):
        test_file = SAMPLE_DIR / "microsoft-sample.docx"
        resp = self.client.metadata.from_file(test_file, magic.from_file(str(test_file), mime=True))

        self.assertEqual(resp.type, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        self.assertEqual(resp.created, datetime(year=2023, month=5, day=17, hour=16, second=41, tzinfo=ZoneInfo("UTC")))

    def test_metadata_from_odt(self):
        test_file = SAMPLE_DIR / "sample.odt"
        resp = self.client.metadata.from_file(test_file, magic.from_file(str(test_file), mime=True))

        self.assertEqual(resp.type, "application/vnd.oasis.opendocument.text")
        self.assertEqual(resp.data["generator"], "LibreOfficeDev/6.0.5.2$Linux_X86_64 LibreOffice_project/")
        self.assertIsNone(resp.created)
