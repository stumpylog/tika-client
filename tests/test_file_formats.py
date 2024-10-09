from datetime import datetime
from pathlib import Path

import magic

from tika_client.client import TikaClient


class TestLibreOfficeFormats:
    def test_parse_libre_office_writer_document(self, tika_client: TikaClient, sample_libre_office_writer_file: Path):
        """
        Test handling of a ODT document produced by LibreOffice
        """
        resp = tika_client.tika.as_html.from_file(
            sample_libre_office_writer_file,
            magic.from_file(str(sample_libre_office_writer_file), mime=True),
        )

        assert resp.type == "application/vnd.oasis.opendocument.text"
        assert resp.content is not None
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
