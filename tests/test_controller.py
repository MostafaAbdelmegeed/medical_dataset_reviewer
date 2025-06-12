from pathlib import Path
from seg_qc_tool.controller import Controller, CONFIG_PATH


def test_discard_current(tmp_path: Path) -> None:
    orig = tmp_path / "orig"
    seg = tmp_path / "seg"
    discard = tmp_path / "discard"
    orig.mkdir()
    seg.mkdir()
    discard.mkdir()

    (orig / "v.npy").write_text("o")
    (seg / "v_seg.npy").write_text("s")

    if CONFIG_PATH.exists():
        CONFIG_PATH.unlink()
    c = Controller()
    c.set_segmentations_dir(seg)
    c.set_originals_dir(orig)
    c.set_discard_dir(discard)

    assert len(c.pairs) == 1
    c.discard_current("bad")
    # segmentation copied
    assert (seg / "v_seg.npy").exists()
    assert (discard / "v_seg.npy").exists()
    # pair still present
    assert c.current_index == 0


def test_discard_current_dicom_slice(tmp_path: Path) -> None:
    from tests.test_io_utils import _write_dcm

    orig = tmp_path / "orig"
    seg = tmp_path / "seg"
    discard = tmp_path / "discard"
    orig.mkdir()
    seg.mkdir()
    discard.mkdir()

    orig_series = orig / "p1"
    seg_series = seg / "p1_seg"
    orig_series.mkdir()
    seg_series.mkdir()
    _write_dcm(orig_series / "0.dcm", 0, instance=1)
    _write_dcm(seg_series / "a.dcm", 1, instance=1)
    _write_dcm(seg_series / "b.dcm", 2, instance=2)

    if CONFIG_PATH.exists():
        CONFIG_PATH.unlink()
    c = Controller()
    c.set_segmentations_dir(seg)
    c.set_originals_dir(orig)
    c.set_discard_dir(discard)
    assert len(c.pairs) == 1

    c.set_slice_index(1)
    c.discard_current("bad slice")

    # both segmentation files remain
    assert (seg_series / "a.dcm").exists()
    assert (seg_series / "b.dcm").exists()
    # copied second slice
    assert (discard / "p1_seg" / "b.dcm").exists()
