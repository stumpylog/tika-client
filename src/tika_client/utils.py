from datetime import datetime
from pathlib import Path
from typing import Dict
from typing import Optional

from httpx import Client


class BaseResponse:
    def __init__(self, data: Dict) -> None:
        self.data = data
        self.__post_init__()

    def __post_init__(self) -> None:
        pass

    def get_optional_int(self, key: str) -> Optional[int]:
        if key not in self.data:  # pragma: no cover
            return None
        return int(self.data[key])

    def get_optional_datetime(self, key: str) -> Optional[datetime]:
        if key not in self.data:  # pragma: no cover
            return None
        # Handle Zulu time as UTC
        return datetime.fromisoformat(self.data[key].replace("Z", "+00:00"))


class BaseResource:
    def __init__(self, client: Client) -> None:
        self.client = client

    def put_multipart(self, endpoint: str, filepath: Path, mime_type: Optional[str] = None) -> Dict:
        with filepath.open("rb") as handle:
            if mime_type is not None:
                files = {"upload-file": (filepath.name, handle, mime_type)}
            else:
                files = {"upload-file": (filepath.name, handle)}  # type: ignore
            resp = self.client.post(endpoint, files=files)
            resp.raise_for_status()
            # Always JSON
            return resp.json()
