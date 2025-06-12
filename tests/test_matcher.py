from pathlib import Path
from seg_qc_tool.matcher import pair_finder
from seg_qc_tool.models import Pair
from tests.test_io_utils import _write_dcm


def test_pair_finder(tmp_path: Path) -> None:
    orig_dir = tmp_path / "orig"
    seg_dir = tmp_path / "seg"
    orig_dir.mkdir()
    seg_dir.mkdir()
    (orig_dir / "patient1.nii").write_text("a")
    (seg_dir / "patient1_seg.nii").write_text("b")

    pairs = pair_finder(orig_dir, seg_dir)
    assert len(pairs) == 1
    assert isinstance(pairs[0], Pair)

def test_strip_suffix():
    from seg_qc_tool.matcher import _strip_suffix
    assert _strip_suffix('file_seg') == 'file'
    assert _strip_suffix('file_mask') == 'file'
    assert _strip_suffix('file_label') == 'file'
    assert _strip_suffix('file') == 'file'


def test_pair_finder_dicom_dir(tmp_path: Path) -> None:
    orig_root = tmp_path / "orig"
    seg_root = tmp_path / "seg"
    orig_root.mkdir()
    seg_root.mkdir()
    series = orig_root / "patient1"
    series.mkdir()
    _write_dcm(series / "0.dcm", 0, instance=1)
    (seg_root / "patient1_seg.nii").write_text("s")
    pairs = pair_finder(orig_root, seg_root)
    assert pairs and pairs[0].original == series


def test_pair_finder_recursive(tmp_path: Path) -> None:
    orig_root = tmp_path / "orig"
    seg_root = tmp_path / "seg"
    orig_root.mkdir()
    seg_root.mkdir()
    (orig_root / "nested").mkdir()
    (seg_root / "nested").mkdir()
    (orig_root / "nested" / "vol.nii").write_text("v")
    (seg_root / "nested" / "vol_seg.nii").write_text("s")
    pairs = pair_finder(orig_root, seg_root)
    assert pairs and pairs[0].original.name == "vol.nii"
