"""I/O utilities for loading medical images."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Tuple, List, Union
from functools import lru_cache

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
    """Load a NIfTI file as a numpy array and close the file handle."""
    img = nib.load(str(path))
    data = img.get_fdata(dtype=np.float32)
    if data.ndim == 4:
        data = data[..., 0]
    if data.ndim == 3:
        data = np.transpose(data, (2, 0, 1))
    # Explicitly close any open file handles held by nibabel
    if hasattr(img, "file_map"):
        for fh in img.file_map.values():
            if fh.fileobj:
                fh.fileobj.close()
    return np.asarray(data)


def load_npy(path: Path) -> np.ndarray:
    """Load a .npy volume."""
    return np.load(str(path))


def load_dicom_series(path: Path, *, return_files: bool = False) -> Union[np.ndarray, Tuple[np.ndarray, List[Path]]]:  # pragma: no cover - heavy I/O
    """Load a DICOM series from a file or directory.

    Parameters
    ----------
    path:
        Directory containing ``.dcm`` files or one file from the series.
    return_files:
        If ``True`` the sorted list of slice file paths is also returned.

    Sorting is based on the ``InstanceNumber`` attribute when available to
    preserve slice order. ``RescaleSlope`` and ``RescaleIntercept`` are applied
    and MONOCHROME1 images are inverted to maintain correct intensity mapping.
    """
    directory = path if path.is_dir() else path.parent

    # Use pydicom directly to keep raw intensities. SimpleITK sometimes applies
    # windowing automatically which can invert the data.

    if pydicom is None:
        raise ImportError("pydicom or SimpleITK required for DICOM loading")

    files = sorted(directory.glob("*.dcm"))
    if not files:
        files = sorted(directory.glob("*.DCM"))
    if not files:
        raise FileNotFoundError("No DICOM files found")

    slices = []
    for f in files:
        with open(f, "rb") as fp:
            ds = pydicom.dcmread(fp)
            inst_num = int(getattr(ds, "InstanceNumber", 0))
            arr = ds.pixel_array.astype(np.float32)
            slope = float(getattr(ds, "RescaleSlope", 1.0))
            intercept = float(getattr(ds, "RescaleIntercept", 0.0))
            arr = arr * slope + intercept
            photometric = getattr(ds, "PhotometricInterpretation", "")
        slices.append((inst_num, arr, photometric, f))

    slices.sort(key=lambda t: t[0])
    arrays = [s[1] for s in slices]
    files = [s[3] for s in slices]
    photometric = slices[0][2] if slices else ""

    volume = np.stack(arrays)
    if photometric == "MONOCHROME1":
        volume = volume.max() - volume
    if return_files:
        return volume, files
    return volume


@lru_cache(maxsize=2)
def load_volume(path: Path) -> np.ndarray:  # pragma: no cover - heavy I/O
    """Load a volume from a supported file path with simple caching."""
    if path.suffix in {".nii", ".nii.gz", ".gz"}:
        return load_nifti(path)
    if path.suffix == ".npy":
        return load_npy(path)
    return load_dicom_series(path)


def normalize_volume(volume: np.ndarray) -> Tuple[np.ndarray, float, float]:
    """Normalize a volume to 0-1 range. Returns volume, min, max."""
    vmin = float(volume.min())
    vmax = float(volume.max())
    if vmax - vmin == 0:
        norm = np.zeros_like(volume, dtype=np.float32)
    else:
        norm = (volume - vmin) / (vmax - vmin)
    return norm.astype(np.float32), vmin, vmax