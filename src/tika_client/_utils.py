from pathlib import Path
from typing import Dict
from typing import Optional

from httpx import Client


class BaseResource:
    def __init__(self, client: Client) -> None:
        self.client = client

    def put_multipart(self, endpoint: str, filepath: Path, mime_type: Optional[str] = None) -> Dict:
        with filepath.open("rb") as handle:
            if mime_type is not None:
                files = {"upload-file": (filepath.name, handle, mime_type)}
            else:
                files = {"upload-file": (filepath.name, handle)}  # type: ignore
            resp = self.client.post(
                endpoint,
                files=files,
                headers={"Content-Disposition": f"attachment; filename={filepath.name}"},
            )
            resp.raise_for_status()
            # Always JSON
            return resp.json()
