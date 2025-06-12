"""I/O utilities for loading medical images."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Tuple

import numpy as np
import nibabel as nib

try:
    import pydicom
    import SimpleITK as sitk
except Exception:  # pragma: no cover - optional deps
    pydicom = None
    sitk = None

logger = logging.getLogger(__name__)


def load_nifti(path: Path) -> np.ndarray:  # pragma: no cover - heavy I/O
    """Load a NIfTI file as a numpy array."""
    img = nib.load(str(path))
    data = img.get_fdata(dtype=np.float32)
    return np.asarray(data)


def load_npy(path: Path) -> np.ndarray:
    """Load a .npy volume."""
    return np.load(str(path))


def load_dicom_series(path: Path) -> np.ndarray:  # pragma: no cover - heavy I/O
    """Load a DICOM series from a file or directory."""
    directory = path if path.is_dir() else path.parent

    if sitk is not None:
        try:
            reader = sitk.ImageSeriesReader()
            series_ids = reader.GetGDCMSeriesIDs(str(directory))
            if series_ids:
                reader.SetFileNames(reader.GetGDCMSeriesFileNames(str(directory)))
                img = reader.Execute()
                array = sitk.GetArrayFromImage(img).astype(np.float32)
                return array
        except Exception:  # pragma: no cover - optional deps
            logger.exception("SimpleITK failed, falling back to pydicom")

    if pydicom is None:
        raise ImportError("pydicom or SimpleITK required for DICOM loading")

    files = sorted(directory.glob("*.dcm"))
    if not files:
        files = sorted(directory.glob("*.DCM"))
    if not files:
        raise FileNotFoundError("No DICOM files found")

    slices = [pydicom.dcmread(str(f)).pixel_array for f in files]
    return np.stack(slices).astype(np.float32)


def normalize_volume(volume: np.ndarray) -> Tuple[np.ndarray, float, float]:
    """Normalize a volume to 0-1 range. Returns volume, min, max."""
    vmin = float(volume.min())
    vmax = float(volume.max())
    if vmax - vmin == 0:
        norm = np.zeros_like(volume, dtype=np.float32)
    else:
        norm = (volume - vmin) / (vmax - vmin)
    return norm.astype(np.float32), vmin, vmax
