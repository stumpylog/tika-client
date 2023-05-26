import logging
from typing import Dict

from httpx import Client

from tika_client._resource_meta import Metadata
from tika_client._resource_recursive import Recursive
from tika_client._resource_tika import Tika


class TikaClient:
    def __init__(self, tika_url: str, timeout: float = 30.0, log_level: int = logging.ERROR):
        # Configure the client
        self._client = Client(base_url=tika_url, timeout=timeout)

        # Set the log level
        logging.getLogger("httpx").setLevel(log_level)
        logging.getLogger("httpcore").setLevel(log_level)

        # Only JSON responses supported
        self._client.headers.update({"Accept": "application/json"})

        # Add the resources
        self.metadata = Metadata(self._client)
        self.tika = Tika(self._client)
        self.rmeta = Recursive(self._client)

    def add_headers(self, header: Dict[str, str]):
        """
        Updates the httpx Client headers with the given values
        """
        self._client.headers.update(header)

    def __enter__(self) -> "TikaClient":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self._client.close()
