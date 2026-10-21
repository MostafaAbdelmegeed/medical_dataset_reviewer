"""Small synthetic volumes for trying the reviewer without a dataset."""

from pathlib import Path

import numpy as np


def create_demo_dataset(root: Path) -> tuple[Path, Path]:
    """Write two paired phantoms: one aligned mask and one displaced mask."""
    originals, segmentations = root / "originals", root / "segmentations"
    originals.mkdir(parents=True, exist_ok=True)
    segmentations.mkdir(parents=True, exist_ok=True)
    z, y, x = np.mgrid[-1:1:48j, -1:1:192j, -1:1:192j]
    outer = (x / .77) ** 2 + (y / .9) ** 2 + (z / 1.05) ** 2 < 1
    inner = (x / .66) ** 2 + (y / .78) ** 2 + (z / .94) ** 2 < 1
    ventricles = (((x - .13) / .10) ** 2 + (y / .22) ** 2 + (z / .7) ** 2 < 1)
    ventricles |= (((x + .13) / .10) ** 2 + (y / .22) ** 2 + (z / .7) ** 2 < 1)
    texture = 7 * np.sin(36 * x + 4 * z) * np.cos(29 * y - 3 * z)
    volume = np.where(outer, 130 + texture, 0)
    volume = np.where(inner, 85 + texture, volume)
    volume = np.where(ventricles & inner, 22, volume).astype(np.float32)
    mask = np.where(inner, 1, 0).astype(np.uint8)
    mask[ventricles] = 0
    for name, segmentation in (("phantom_aligned", mask),
                               ("phantom_displaced", np.roll(mask, 18, axis=2))):
        np.save(originals / f"{name}.npy", volume)
        np.save(segmentations / f"{name}_seg.npy", segmentation)
    return originals, segmentations
