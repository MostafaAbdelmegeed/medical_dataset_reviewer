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

## Design decisions

- **PySide6** provides a permissive Qt binding for GUI widgets.
- **nibabel**, **pydicom**, and **SimpleITK** handle medical image formats.
- **concurrent.futures** keeps the UI responsive when loading data.
