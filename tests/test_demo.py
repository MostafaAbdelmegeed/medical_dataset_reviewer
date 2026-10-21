from pathlib import Path

import numpy as np
from seg_qc_tool.controller import Controller
from seg_qc_tool.demo import create_demo_dataset
from seg_qc_tool.matcher import pair_finder


def test_demo_provides_paired_aligned_and_displaced_masks(tmp_path):
    originals, segmentations = create_demo_dataset(tmp_path)
    pairs = pair_finder(originals, segmentations)
    assert len(pairs) == 2
    masks = {pair.original.stem: np.load(pair.segmentation) for pair in pairs}
    aligned = masks["phantom_aligned"]
    displaced = masks["phantom_displaced"]
    assert aligned.shape == (48, 192, 192)
    assert np.array_equal(displaced, np.roll(aligned, 18, axis=2))
    assert 0 < aligned.sum() < aligned.size


def test_demo_settings_do_not_persist(tmp_path):
    from seg_qc_tool import controller as controller_module
    controller = Controller(persist_settings=False)
    try:
        controller.set_discard_dir(tmp_path / "discard")
        assert not controller_module.CONFIG_PATH.exists()
    finally:
        controller.executor.shutdown(wait=True)


def test_pair_finder_handles_multiple_compressed_nifti_files(tmp_path):
    originals, segmentations = tmp_path / "originals", tmp_path / "segmentations"
    originals.mkdir()
    segmentations.mkdir()
    for name in ("case_a", "case_b"):
        (originals / f"{name}.nii.gz").touch()
        (segmentations / f"{name}_seg.nii.gz").touch()
    pairs = pair_finder(originals, segmentations)
    assert len(pairs) == 2
    assert all(pair.segmentation.name == pair.original.name.replace(".nii.gz", "_seg.nii.gz") for pair in pairs)
