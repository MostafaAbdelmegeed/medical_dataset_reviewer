"""Utilities for pairing original and segmentation files."""

from __future__ import annotations

from difflib import SequenceMatcher
from pathlib import Path
from typing import Iterable, List

from .models import Pair

try:
    import Levenshtein  # type: ignore
    def distance(a: str, b: str) -> int:
        return Levenshtein.distance(a, b)
except Exception:  # pragma: no cover - optional
    def distance(a: str, b: str) -> int:
        matcher = SequenceMatcher(a=a, b=b)
        return int((1 - matcher.ratio()) * max(len(a), len(b)))


_SUFFIXES = ["_seg", "_mask", "_label"]


def _strip_suffix(name: str) -> str:
    for suf in _SUFFIXES:
        if name.endswith(suf):
            return name[: -len(suf)]
    return name


def pair_finder(original_dir: Path, seg_dir: Path, max_dist: int = 2) -> List[Pair]:
    """Pair files in two directories using fuzzy matching."""
    originals = list(original_dir.glob("*"))
    segs = list(seg_dir.glob("*"))
    pairs = []
    used_segs = set()
    for orig in originals:
        base_orig = _strip_suffix(orig.stem)
        best = None
        best_dist = max_dist + 1
        for seg in segs:
            if seg in used_segs:
                continue
            base_seg = _strip_suffix(seg.stem)
            dist = distance(base_orig, base_seg)
            if dist < best_dist:
                best = seg
                best_dist = dist
        if best is not None and best_dist <= max_dist:
            pairs.append(Pair(orig, best))
            used_segs.add(best)
    return pairs
