from datetime import datetime
from datetime import timezone
from pathlib import Path

import httpx
import magic
import pytest
from pytest_httpx import HTTPXMock

from tika_client.client import TikaClient


class TestMetadataResource:
    def test_metadata_from_docx(self, tika_client: TikaClient, sample_google_docs_to_docx_file: Path):
        """
        Test parsing of a DOCX produced by Google Docs conversion
        """

        resp = tika_client.metadata.from_file(
            sample_google_docs_to_docx_file,
            magic.from_file(str(sample_google_docs_to_docx_file), mime=True),
        )

        assert resp.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        assert resp.created is None

    def test_metadata_from_docx_no_mime(self, tika_client: TikaClient, sample_google_docs_to_docx_file: Path):
        """
        Test parsing of a DOCX produced by Google Docs conversion, when no mime type is provided
        """

        resp = tika_client.metadata.from_file(sample_google_docs_to_docx_file)

        assert resp.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        assert resp.created is None

    def test_metadata_from_word_docx(self, tika_client: TikaClient, sample_docx_file: Path):
        """
        Test parsing of a DOCX produced by Microsoft Word
        """
        resp = tika_client.metadata.from_file(sample_docx_file, magic.from_file(str(sample_docx_file), mime=True))

        assert resp.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        assert resp.created == datetime(year=2023, month=5, day=17, hour=16, minute=41, tzinfo=timezone.utc)
        assert resp.modified == datetime(year=2023, month=5, day=17, hour=16, minute=44, tzinfo=timezone.utc)

    def test_metadata_from_odt(self, tika_client: TikaClient, sample_google_docs_to_libre_office_writer_file: Path):
        """
        Test parsing of a ODT produced by Google Docs conversion
        """
        resp = tika_client.metadata.from_file(
            sample_google_docs_to_libre_office_writer_file,
            magic.from_file(str(sample_google_docs_to_libre_office_writer_file), mime=True),
        )

        assert resp.type == "application/vnd.oasis.opendocument.text"
        assert resp.data["generator"] == "LibreOfficeDev/6.0.5.2$Linux_X86_64 LibreOffice_project/"
        assert resp.created is None

    def test_metadata_from_doc(self, tika_client: TikaClient, sample_doc_file: Path):
        """
        Test parsing of a DOC produced by Google Docs conversion
        """
        resp = tika_client.metadata.from_file(sample_doc_file, magic.from_file(str(sample_doc_file), mime=True))

        assert resp.type == "application/msword"
        assert resp.language == "en"

    def test_http_error(
        self,
        httpx_mock: HTTPXMock,
        tika_host: str,
        sample_google_docs_to_libre_office_writer_file: Path,
    ):
        """
        Test handling of HTTP errors returned from Tika
        """

        httpx_mock.add_response(status_code=500)
        with pytest.raises(httpx.HTTPStatusError) as err, TikaClient(tika_url=tika_host) as client:
            client.metadata.from_file(sample_google_docs_to_libre_office_writer_file)
        assert err.value.response.status_code == httpx.codes.INTERNAL_SERVER_ERROR
