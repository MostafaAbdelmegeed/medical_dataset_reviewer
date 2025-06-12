import numpy as np
from pathlib import Path
from seg_qc_tool.io_utils import normalize_volume, load_npy

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
