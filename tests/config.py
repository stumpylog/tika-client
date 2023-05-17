from pathlib import Path
from typing import Final

TIKA_URL: Final[str] = "http://localhost:9998"

SAMPLE_DIR: Final[Path] = Path(__file__).parent.resolve() / "samples"