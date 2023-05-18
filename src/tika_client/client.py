from httpx import Client

from tika_client._resource_meta import Metadata
from tika_client._resource_tika import Tika


class TikaClient(Client):
    def __init__(self, timeout: float = 30.0, *args, **kwargs):  # type: ignore
        super().__init__(*args, **kwargs, timeout=timeout)
        # Only JSON responses supported
        self.headers.update({"Accept": "application/json"})

        self.metadata = Metadata(self)
        self.tika = Tika(self)
