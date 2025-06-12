"""Controller connecting GUI and backend."""

from __future__ import annotations

import csv
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List
from concurrent.futures import ThreadPoolExecutor, Future

from PySide6 import QtCore

from .io_utils import load_dicom_series, load_nifti, load_npy, normalize_volume
from .matcher import pair_finder
from .models import Pair, Settings

logger = logging.getLogger(__name__)

CONFIG_PATH = Path.home() / ".seg_qc_tool" / "config.json"


class Controller(QtCore.QObject):
    pair_changed = QtCore.Signal(Pair)
    slice_changed = QtCore.Signal(int)
    overlay_toggled = QtCore.Signal(bool)

    def __init__(self) -> None:
        super().__init__()
        self.settings = self.load_settings()
        self.pairs: List[Pair] = []
        self.current_index = -1
        self.executor = ThreadPoolExecutor(max_workers=2)

    # Settings -------------------------------------------------
    def load_settings(self) -> Settings:
        if CONFIG_PATH.exists():
            try:
                data = json.loads(CONFIG_PATH.read_text())
                return Settings(
                    originals_dir=Path(data.get("originals_dir")) if data.get("originals_dir") else None,
                    segmentations_dir=Path(data.get("segmentations_dir")) if data.get("segmentations_dir") else None,
                    discard_dir=Path(data.get("discard_dir")) if data.get("discard_dir") else None,
                    window_size=tuple(data.get("window_size")) if data.get("window_size") else None,
                    brightness=data.get("brightness", 0.5),
                    contrast=data.get("contrast", 0.5),
                )
            except Exception as e:  # pragma: no cover
                logger.warning("Failed to load settings: %s", e)
        return Settings()

    def save_settings(self) -> None:
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        CONFIG_PATH.write_text(json.dumps(self.settings.__dict__, default=str))

    # Pairing --------------------------------------------------
    def load_pairs(self) -> None:
        if not self.settings.originals_dir or not self.settings.segmentations_dir:
            return
        pairs = pair_finder(self.settings.originals_dir, self.settings.segmentations_dir)
        self.pairs = pairs
        self.current_index = 0 if pairs else -1
        if pairs:
            self.pair_changed.emit(pairs[0])

    def next_pair(self) -> None:
        if self.current_index + 1 < len(self.pairs):
            self.current_index += 1
            self.pair_changed.emit(self.pairs[self.current_index])

    def prev_pair(self) -> None:
        if self.current_index > 0:
            self.current_index -= 1
            self.pair_changed.emit(self.pairs[self.current_index])

    # Discard --------------------------------------------------
    def discard_current(self, comment: str = "") -> None:
        if self.current_index == -1 or not self.settings.discard_dir:
            return
        pair = self.pairs[self.current_index]
        rel = pair.segmentation.relative_to(self.settings.segmentations_dir)
        target = self.settings.discard_dir / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        pair.segmentation.rename(target)
        with open("discard_log.csv", "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([datetime.now().isoformat(), str(pair.original), str(pair.segmentation), comment])
        self.next_pair()
