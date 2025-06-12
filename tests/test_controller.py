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
    # segmentation moved
    assert not (seg / "v_seg.npy").exists()
    assert (discard / "v_seg.npy").exists()
    # no pairs left
    assert c.current_index == -1
