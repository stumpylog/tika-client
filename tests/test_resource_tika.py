import magic

from tests.conftest import SAMPLE_DIR
from tika_client.client import TikaClient
from tika_client.data_models import Document


class TestParseFormatted:
    def test_parse_docx(self, tika_client: TikaClient):
        test_file = SAMPLE_DIR / "sample.docx"
        resp = tika_client.tika.as_html.from_file(test_file, magic.from_file(str(test_file), mime=True))

        assert isinstance(resp, Document)
        assert resp.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        assert "<body><p>This is an DOCX test document, also made September 14, 2022</p>\n</body>" in resp.content

    def test_parse_docx_no_mime(self, tika_client: TikaClient):
        test_file = SAMPLE_DIR / "sample.docx"
        resp = tika_client.tika.as_html.from_file(test_file)

        assert isinstance(resp, Document)
        assert resp.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        assert "<body><p>This is an DOCX test document, also made September 14, 2022</p>\n</body>" in resp.content

    def test_parse_microsoft_word_docx(self, tika_client: TikaClient):
        test_file = SAMPLE_DIR / "microsoft-sample.docx"
        resp = tika_client.tika.as_html.from_file(test_file, magic.from_file(str(test_file), mime=True))

        assert isinstance(resp, Document)
        assert resp.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        assert (
            "<body><p>This is a sample document, generated by Microsoft Office on Wednesday, May 17, 2023.</p>\n<p>It is in English.</p>\n</body>"  # noqa: E501
            in resp.content
        )

    def test_parse_odt(self, tika_client: TikaClient):
        test_file = SAMPLE_DIR / "sample.odt"
        resp = tika_client.tika.as_html.from_file(test_file, magic.from_file(str(test_file), mime=True))

        assert isinstance(resp, Document)
        assert resp.type == "application/vnd.oasis.opendocument.text"
        assert "<body><p>This is an ODT test document, created September 14, 2022</p>\n</body>" in resp.content


class TestParsePlain:
    def test_parse_docx(self, tika_client: TikaClient):
        test_file = SAMPLE_DIR / "sample.docx"

        resp = tika_client.tika.as_text.from_file(test_file, magic.from_file(str(test_file), mime=True))

        assert isinstance(resp, Document)
        assert resp.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        assert "This is an DOCX test document, also made September 14, 2022" in resp.content

    def test_parse_odt(self, tika_client: TikaClient):
        test_file = SAMPLE_DIR / "sample.odt"

        resp = tika_client.tika.as_text.from_file(test_file, magic.from_file(str(test_file), mime=True))

        assert isinstance(resp, Document)
        assert resp.type == "application/vnd.oasis.opendocument.text"
        assert "This is an ODT test document, created September 14, 2022" in resp.content


class TestParseContentPlain:
    def test_parse_docx_bytes(self, tika_client: TikaClient):
        test_file = SAMPLE_DIR / "sample.docx"
        buffer = test_file.read_bytes()

        resp = tika_client.tika.as_text.from_buffer(buffer)

        assert isinstance(resp, Document)
        assert resp.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        assert "This is an DOCX test document, also made September 14, 2022" in resp.content

    def test_parse_odt_bytes(self, tika_client: TikaClient):
        test_file = SAMPLE_DIR / "sample.odt"
        buffer = test_file.read_bytes()

        resp = tika_client.tika.as_text.from_buffer(buffer)

        assert isinstance(resp, Document)
        assert resp.type == "application/vnd.oasis.opendocument.text"
        assert "This is an ODT test document, created September 14, 2022" in resp.content

    def test_parse_buffer_text_content(self, tika_client: TikaClient):
        test_file = SAMPLE_DIR / "sample.html"
        buffer = test_file.read_text()

        resp = tika_client.tika.as_text.from_buffer(buffer)

        assert resp.type == "text/html; charset=UTF-8"
        assert resp.parsers == ["org.apache.tika.parser.DefaultParser", "org.apache.tika.parser.html.HtmlParser"]
        assert "Hello world! This is HTML5 content in a file for" in resp.data["X-TIKA:content"]
        assert resp.data["dc:title"] == "This Is A Test"
        assert resp.data["description"] == "A sample HTML file"
