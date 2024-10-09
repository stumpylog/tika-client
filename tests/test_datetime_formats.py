from datetime import datetime
from datetime import timedelta
from datetime import timezone
from pathlib import Path

import magic
import pytest
from pytest_httpx import HTTPXMock

from tika_client.client import TikaClient
from tika_client.data_models import DublinCoreKey
from tika_client.data_models import TikaKey


class TestDateTimeFormat:
    def test_parse_offset_date_format_utc(
        self,
        tika_client: TikaClient,
        sample_libre_office_writer_file: Path,
        httpx_mock: HTTPXMock,
    ):
        """
        Test the datetime parsing properly handles a time with a UTC timezone in the +xx:yy format
        """

        httpx_mock.add_response(
            json={TikaKey.ContentType: "test", TikaKey.Parsers: [], DublinCoreKey.Created: "2023-05-17T16:30:44+00:00"},
        )

        resp = tika_client.metadata.from_file(
            sample_libre_office_writer_file,
            magic.from_file(str(sample_libre_office_writer_file), mime=True),
        )

        assert resp.created == datetime(
            year=2023,
            month=5,
            day=17,
            hour=16,
            minute=30,
            second=44,
            tzinfo=timezone.utc,
        )

    def test_parse_offset_date_format_zulu(
        self,
        tika_client: TikaClient,
        sample_libre_office_writer_file: Path,
        httpx_mock: HTTPXMock,
    ):
        """
        Test the datetime parsing properly handles a time with a UTC timezone in the Z format
        """

        httpx_mock.add_response(
            json={TikaKey.ContentType: "test", TikaKey.Parsers: [], DublinCoreKey.Created: "2023-01-17T16:35:44Z"},
        )

        resp = tika_client.metadata.from_file(
            sample_libre_office_writer_file,
            magic.from_file(str(sample_libre_office_writer_file), mime=True),
        )

        assert resp.created == datetime(
            year=2023,
            month=1,
            day=17,
            hour=16,
            minute=35,
            second=44,
            tzinfo=timezone.utc,
        )

    def test_parse_offset_date_format_positive(
        self,
        tika_client: TikaClient,
        sample_libre_office_writer_file: Path,
        httpx_mock: HTTPXMock,
    ):
        """
        Test the datetime parsing properly handles a time with a timezone in the +xx:yy format offset from UTC
        """

        httpx_mock.add_response(
            json={TikaKey.ContentType: "test", TikaKey.Parsers: [], DublinCoreKey.Created: "2023-06-17T16:30:44+08:00"},
        )

        resp = tika_client.metadata.from_file(
            sample_libre_office_writer_file,
            magic.from_file(str(sample_libre_office_writer_file), mime=True),
        )

        assert resp.created == pytest.approx(
            datetime(year=2023, month=6, day=17, hour=16, minute=30, second=44, tzinfo=timezone(timedelta(hours=8))),
            rel=timedelta(seconds=1),
        )

    def test_parse_offset_date_format_negative(
        self,
        tika_client: TikaClient,
        sample_libre_office_writer_file: Path,
        httpx_mock: HTTPXMock,
    ):
        """
        Test the datetime parsing properly handles a time with a timezone in the -xx:yy format offset from UTC
        """

        httpx_mock.add_response(
            json={TikaKey.ContentType: "test", TikaKey.Parsers: [], DublinCoreKey.Created: "2023-06-17T16:30:44-08:00"},
        )

        resp = tika_client.metadata.from_file(
            sample_libre_office_writer_file,
            magic.from_file(str(sample_libre_office_writer_file), mime=True),
        )

        assert resp.created == pytest.approx(
            datetime(
                year=2023,
                month=6,
                day=17,
                hour=16,
                minute=30,
                second=44,
                tzinfo=timezone(timedelta(hours=-8)),
            ),
            rel=timedelta(seconds=1),
        )

    def test_parse_offset_date_format_python_isoformat(
        self,
        tika_client: TikaClient,
        sample_libre_office_writer_file: Path,
        httpx_mock: HTTPXMock,
    ):
        """
        Test the datetime parsing properly handles a time with a timezone in the ISO 8061 format (as done by Python)
        """

        expected = datetime.now(tz=timezone.utc)

        httpx_mock.add_response(
            json={TikaKey.ContentType: "test", TikaKey.Parsers: [], DublinCoreKey.Created: expected.isoformat()},
        )

        resp = tika_client.metadata.from_file(
            sample_libre_office_writer_file,
            magic.from_file(str(sample_libre_office_writer_file), mime=True),
        )

        assert resp.created == pytest.approx(expected, rel=timedelta(seconds=1))

    def test_parse_offset_date_no_match(
        self,
        tika_client: TikaClient,
        sample_libre_office_writer_file: Path,
        httpx_mock: HTTPXMock,
    ):
        """
        Test the datetime parsing properly handles a time string which doesn't match the correct formats
        """

        httpx_mock.add_response(
            json={TikaKey.ContentType: "test", TikaKey.Parsers: [], DublinCoreKey.Created: "202-06-17T16:30:44-0"},
        )

        resp = tika_client.metadata.from_file(
            sample_libre_office_writer_file,
            magic.from_file(str(sample_libre_office_writer_file), mime=True),
        )

        assert resp.created is None
