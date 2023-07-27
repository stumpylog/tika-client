from datetime import datetime

import magic

from tests.conftest import SAMPLE_DIR
from tika_client.client import TikaClient


class TestLibreOfficeFormats:
    def test_parse_libre_office_writer_document(self, tika_client: TikaClient):
        """
        Test handling of a ODT document produced by LibreOffice
        """
        test_file = SAMPLE_DIR / "sample-libre-office.odt"
        resp = tika_client.tika.as_html.from_file(test_file, magic.from_file(str(test_file), mime=True))

        assert resp.type == "application/vnd.oasis.opendocument.text"
        assert (
            "<body><p>This is a document created by LibreOffice Writer 7.5.12, on July 19th, 2023</p>\n</body>"
            in resp.content
        )
        assert resp.content_length == 11149
        assert resp.created is not None
        assert resp.created == datetime(
            year=2023,
            month=7,
            day=19,
            hour=11,
            minute=30,
            second=44,
            microsecond=719000,
            tzinfo=None,
        )
