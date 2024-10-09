import logging
from pathlib import Path
from typing import Generator

import pytest
from pytest_docker.plugin import Services

from tika_client.client import TikaClient

logger = logging.getLogger("tika-client.tests")


@pytest.fixture(scope="session")
def docker_compose_file() -> Path:
    return Path(__file__).parent / "docker" / "docker-compose.ci-test.yml"


@pytest.fixture(scope="session")
def tika_host(docker_services: Services, docker_ip: str) -> str:
    def is_responsive(url):
        import httpx

        try:
            response = httpx.get(url)
        except httpx.HTTPError:
            logger.exception("Error connecting to service")
            return False
        else:
            return response.status_code == httpx.codes.OK

    url = f"http://{docker_ip}:{docker_services.port_for('tika', 9998)}"

    docker_services.wait_until_responsive(
        timeout=30.0,
        pause=1,
        check=lambda: is_responsive(url),
    )
    return url


@pytest.fixture(scope="session")
def samples_dir() -> Path:
    return Path(__file__).parent.resolve() / "samples"


@pytest.fixture(scope="session")
def sample_libre_office_writer_file(samples_dir: Path) -> Path:
    return samples_dir / "sample-libre-office.odt"


@pytest.fixture(scope="session")
def sample_google_docs_to_libre_office_writer_file(samples_dir: Path) -> Path:
    return samples_dir / "sample.odt"


@pytest.fixture(scope="session")
def sample_google_docs_to_docx_file(samples_dir: Path) -> Path:
    return samples_dir / "sample.docx"


@pytest.fixture(scope="session")
def sample_docx_file(samples_dir: Path) -> Path:
    return samples_dir / "microsoft-sample.docx"


@pytest.fixture(scope="session")
def sample_doc_file(samples_dir: Path) -> Path:
    return samples_dir / "sample.doc"


@pytest.fixture(scope="session")
def sample_html_file(samples_dir: Path) -> Path:
    return samples_dir / "sample.html"


@pytest.fixture(scope="session")
def sample_office_doc_with_images_file(samples_dir: Path) -> Path:
    return samples_dir / "test-document-images.odt"


@pytest.fixture(scope="session")
def sample_jpeg_file(samples_dir: Path) -> Path:
    return samples_dir / "sample.jpg"


@pytest.fixture(scope="session")
def sample_png_file(samples_dir: Path) -> Path:
    return samples_dir / "sample.png"


@pytest.fixture(scope="session")
def sample_ods_file(samples_dir: Path) -> Path:
    return samples_dir / "sample-spreadsheet.ods"


@pytest.fixture(scope="session")
def sample_xlsx_file(samples_dir: Path) -> Path:
    return samples_dir / "sample-spreadsheet.xlsx"


@pytest.fixture
def tika_client(tika_host: str) -> Generator[TikaClient, None, None]:
    with TikaClient(tika_url=tika_host, log_level=logging.INFO) as client:
        yield client


@pytest.fixture
def tika_client_compressed(tika_host: str) -> Generator[TikaClient, None, None]:
    with TikaClient(tika_url=tika_host, log_level=logging.INFO, compress=True) as client:
        yield client
