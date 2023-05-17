from datetime import datetime
from typing import Dict
from typing import Optional


class BaseResponse:
    def __init__(self, data: Dict) -> None:
        self.data = data

    def get_optional_int(self, key: str) -> Optional[int]:
        if key not in self.data:
            return None
        return int(self.data[key])

    def get_optional_datetime(self, key: str) -> Optional[datetime]:
        if key not in self.data:
            return None
        # Handle Zulu time as UTC
        return datetime.fromisoformat(self.data[key].replace("Z", "+00:00"))
