import numpy as np
from pathlib import Path
from seg_qc_tool.io_utils import normalize_volume, load_npy, load_dicom_series, load_nifti
import nibabel as nib
import pydicom
from pydicom.dataset import Dataset, FileMetaDataset, FileDataset
import pydicom.uid

def test_normalize_volume(tmp_path: Path) -> None:
    vol = np.array([0, 1, 2], dtype=np.float32)
    norm, vmin, vmax = normalize_volume(vol)
    assert vmin == 0
    assert vmax == 2
    assert np.allclose(norm, vol / 2)

def test_load_npy(tmp_path: Path) -> None:
    arr = np.arange(6, dtype=np.float32).reshape(2, 3)
    file = tmp_path / "arr.npy"
    np.save(file, arr)
    loaded = load_npy(file)
    assert np.array_equal(loaded, arr)


def _write_dcm(path: Path, value: int, photometric: str = "MONOCHROME2", instance: int = 0) -> None:
    meta = FileMetaDataset()
    meta.TransferSyntaxUID = pydicom.uid.ExplicitVRLittleEndian
    ds = FileDataset(str(path), {}, file_meta=meta, preamble=b"\0" * 128)
    ds.is_little_endian = True
    ds.is_implicit_VR = False
    ds.Rows = 2
    ds.Columns = 2
    ds.PhotometricInterpretation = photometric
    ds.InstanceNumber = instance
    ds.SamplesPerPixel = 1
    ds.BitsAllocated = 8
    ds.BitsStored = 8
    ds.HighBit = 7
    ds.PixelRepresentation = 0
    ds.PixelData = (np.full((2, 2), value, dtype=np.uint8)).tobytes()
    ds.save_as(str(path))


def test_load_dicom_series_from_file(tmp_path: Path) -> None:
    series = tmp_path / "series"
    series.mkdir()
    _write_dcm(series / "0.dcm", 0, instance=1)
    _write_dcm(series / "1.dcm", 1, instance=2)
    volume = load_dicom_series(series / "0.dcm")
    assert volume.shape[0] == 2
    volume2, files = load_dicom_series(series, return_files=True)
    assert len(files) == 2
    assert volume2.shape == volume.shape


def test_load_dicom_series_monochrome1(tmp_path: Path) -> None:
    series = tmp_path / "mono1"
    series.mkdir()
    _write_dcm(series / "b.dcm", 10, photometric="MONOCHROME1", instance=2)
    _write_dcm(series / "a.dcm", 20, photometric="MONOCHROME1", instance=1)
    volume = load_dicom_series(series)
    # Files were written out of order but should be sorted by InstanceNumber
    assert volume.shape[0] == 2
    # Intensity should be inverted
    assert volume.max() == 10


def test_load_nifti_transpose(tmp_path: Path) -> None:
    arr = np.arange(27, dtype=np.float32).reshape(3, 3, 3)
    img = nib.Nifti1Image(arr, np.eye(4))
    file = tmp_path / "vol.nii"
    nib.save(img, str(file))
    loaded = load_nifti(file)
    assert loaded.shape == (3, 3, 3)
    assert np.array_equal(loaded, arr.transpose(2, 0, 1))
