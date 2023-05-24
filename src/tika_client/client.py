from httpx import Client

from tika_client._resource_meta import Metadata
from tika_client._resource_recursive import Recursive
from tika_client._resource_tika import Tika


class TikaClient:
    def __init__(self, tika_url: str, timeout: float = 30.0):
        # Configure the client
        self._client = Client(base_url=tika_url, timeout=timeout)

        # Only JSON responses supported
        self._client.headers.update({"Accept": "application/json"})

        # Add the resources
        self.metadata = Metadata(self._client)
        self.tika = Tika(self._client)
        self.rmeta = Recursive(self._client)

    def __enter__(self) -> "TikaClient":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:  # type: ignore
        self._client.close()
