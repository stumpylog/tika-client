import pytest

from tika_rest_client.client import TikaClient

from .config import TIKA_URL


@pytest.fixture()
def tika_client() -> TikaClient:
    with TikaClient(base_url=TIKA_URL) as client:
        yield client
