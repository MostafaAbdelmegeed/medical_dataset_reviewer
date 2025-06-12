from pathlib import Path
from seg_qc_tool.matcher import pair_finder
from seg_qc_tool.models import Pair


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
