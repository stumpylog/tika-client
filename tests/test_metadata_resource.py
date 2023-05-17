from unittest import TestCase

import magic

from tika_rest_client.client import TikaClient

from .config import SAMPLE_DIR
from .config import TIKA_URL


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
        self.client.metadata.from_file(test_file, magic.from_file(str(test_file), mime=True))
        self.assertTrue(False)

    def test_metadata_from_word_docx(self):
        test_file = SAMPLE_DIR / "microsoft-sample.docx"
        self.client.metadata.from_file(test_file, magic.from_file(str(test_file), mime=True))
        self.assertTrue(False)

    def test_metadata_from_odt(self):
        test_file = SAMPLE_DIR / "sample.odt"
        self.client.metadata.from_file(test_file, magic.from_file(str(test_file), mime=True))
        self.assertTrue(False)
