import logging
import os
from pathlib import Path
from typing import Final

import pytest

from tika_client.client import TikaClient

TIKA_URL: Final[str] = os.getenv("TIKA_URL", "http://localhost:9998")

SAMPLE_DIR: Final[Path] = Path(__file__).parent.resolve() / "samples"


@pytest.fixture()
def tika_client() -> TikaClient:
    with TikaClient(tika_url=TIKA_URL, log_level=logging.INFO) as client:
        yield client


@pytest.fixture()
def tika_client_compressed() -> TikaClient:
    with TikaClient(tika_url=TIKA_URL, log_level=logging.INFO, compress=True) as client:
        yield client
