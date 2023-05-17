from typing import Dict
from typing import Optional


def get_optional_int(data: Dict, key: str) -> Optional[int]:
    if key not in data:
        return None
    return int(data[key])
