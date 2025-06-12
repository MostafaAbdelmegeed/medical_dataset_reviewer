# seg_qc_tool

A simple tool to review segmentation volumes alongside original medical images.

## Setup

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python -m seg_qc_tool
```

## Demo

![demo](resources/demo.gif)

Use the **File** menu to select your originals, segmentations, and discard
folders.

## Folder layout

```
dataset/
  originals/
    patient1/                # DICOM series directory
      0.dcm
      1.dcm
    patient2.nii.gz          # Single NIfTI volume
  segmentations/
    patient1_seg/            # Matching DICOM series
      0.dcm
      1.dcm
    patient2_seg.nii.gz      # Matching NIfTI file
```

The application pairs files by matching the base names of volumes
(e.g. `patient1` ↔ `patient1_seg`). Nested folders are scanned
recursively, so the structure under the segmentations folder should mirror the
originals folder.

## Design decisions

- **PySide6** provides a permissive Qt binding for GUI widgets.
- **nibabel**, **pydicom**, and **SimpleITK** handle medical image formats.
- **concurrent.futures** keeps the UI responsive when loading data.
