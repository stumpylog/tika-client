from datetime import datetime
from datetime import timedelta
from datetime import timezone

import magic
from pytest_httpx import HTTPXMock

from tests.conftest import SAMPLE_DIR
from tika_client.client import TikaClient
from tika_client.data_models import DublinCoreKey
from tika_client.data_models import TikaKey


class TestDateTimeFormat:
    def test_parse_offset_date_format_utc(self, tika_client: TikaClient, httpx_mock: HTTPXMock):
        """
        Test the datetime parsing properly handles a time with a UTC timezone in the +xx:yy format
        """
        test_file = SAMPLE_DIR / "sample-libre-office.odt"

        httpx_mock.add_response(
            json={TikaKey.ContentType: "test", TikaKey.Parsers: [], DublinCoreKey.Created: "2023-05-17T16:30:44+00:00"},
        )

        resp = tika_client.metadata.from_file(test_file, magic.from_file(str(test_file), mime=True))

        assert resp.created == datetime(
            year=2023,
            month=5,
            day=17,
            hour=16,
            minute=30,
            second=44,
            tzinfo=timezone.utc,
        )

    def test_parse_offset_date_format_zulu(self, tika_client: TikaClient, httpx_mock: HTTPXMock):
        """
        Test the datetime parsing properly handles a time with a UTC timezone in the Z format
        """
        test_file = SAMPLE_DIR / "sample-libre-office.odt"

        httpx_mock.add_response(
            json={TikaKey.ContentType: "test", TikaKey.Parsers: [], DublinCoreKey.Created: "2023-01-17T16:35:44Z"},
        )

        resp = tika_client.metadata.from_file(test_file, magic.from_file(str(test_file), mime=True))

        assert resp.created == datetime(
            year=2023,
            month=1,
            day=17,
            hour=16,
            minute=35,
            second=44,
            tzinfo=timezone.utc,
        )

    def test_parse_offset_date_format_positive(self, tika_client: TikaClient, httpx_mock: HTTPXMock):
        """
        Test the datetime parsing properly handles a time with a timezone in the +xx:yy format offset from UTC
        """
        test_file = SAMPLE_DIR / "sample-libre-office.odt"

        httpx_mock.add_response(
            json={TikaKey.ContentType: "test", TikaKey.Parsers: [], DublinCoreKey.Created: "2023-06-17T16:30:44+08:00"},
        )

        resp = tika_client.metadata.from_file(test_file, magic.from_file(str(test_file), mime=True))

        assert resp.created == datetime(
            year=2023,
            month=6,
            day=17,
            hour=16,
            minute=30,
            second=44,
            tzinfo=timezone(timedelta(hours=8)),
        )

    def test_parse_offset_date_format_negative(self, tika_client: TikaClient, httpx_mock: HTTPXMock):
        """
        Test the datetime parsing properly handles a time with a timezone in the -xx:yy format offset from UTC
        """
        test_file = SAMPLE_DIR / "sample-libre-office.odt"

        httpx_mock.add_response(
            json={TikaKey.ContentType: "test", TikaKey.Parsers: [], DublinCoreKey.Created: "2023-06-17T16:30:44-08:00"},
        )

        resp = tika_client.metadata.from_file(test_file, magic.from_file(str(test_file), mime=True))

        assert resp.created == datetime(
            year=2023,
            month=6,
            day=17,
            hour=16,
            minute=30,
            second=44,
            tzinfo=timezone(timedelta(hours=-8)),
        )

    def test_parse_offset_date_format_python_isoformat(self, tika_client: TikaClient, httpx_mock: HTTPXMock):
        """
        Test the datetime parsing properly handles a time with a timezone in the ISO 8061 format (as done by Python)
        """
        test_file = SAMPLE_DIR / "sample-libre-office.odt"

        expected = datetime.now(tz=timezone.utc)

        httpx_mock.add_response(
            json={TikaKey.ContentType: "test", TikaKey.Parsers: [], DublinCoreKey.Created: expected.isoformat()},
        )

        resp = tika_client.metadata.from_file(test_file, magic.from_file(str(test_file), mime=True))

        assert resp.created == expected

    def test_parse_offset_date_no_match(self, tika_client: TikaClient, httpx_mock: HTTPXMock):
        """
        Test the datetime parsing properly handles a time string which doesn't match the correct formats
        """
        test_file = SAMPLE_DIR / "sample-libre-office.odt"

        httpx_mock.add_response(
            json={TikaKey.ContentType: "test", TikaKey.Parsers: [], DublinCoreKey.Created: "202-06-17T16:30:44-0"},
        )

        resp = tika_client.metadata.from_file(test_file, magic.from_file(str(test_file), mime=True))

        assert resp.created is None
