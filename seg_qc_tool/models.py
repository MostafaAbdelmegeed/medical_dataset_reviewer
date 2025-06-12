from dataclasses import dataclass
from pathlib import Path
from typing import Optional

@dataclass
class Pair:
    """Represents a pair of original and segmentation files."""
    original: Path
    segmentation: Path

@dataclass
class Settings:
    """Persisted application settings."""
    originals_dir: Optional[Path] = None
    segmentations_dir: Optional[Path] = None
    discard_dir: Optional[Path] = None
    window_size: Optional[tuple[int, int]] = None
    brightness: float = 0.5
    contrast: float = 0.5
