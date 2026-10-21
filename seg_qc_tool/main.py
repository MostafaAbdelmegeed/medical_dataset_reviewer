"""Entry point for seg_qc_tool."""

from __future__ import annotations

import sys
import argparse
from tempfile import TemporaryDirectory
from pathlib import Path

# Allow running this file directly without installing the package
if __package__ is None:  # pragma: no cover - simple path fix
    sys.path.append(str(Path(__file__).resolve().parent.parent))

from PySide6 import QtWidgets

# Use absolute imports so running this file directly works too
from seg_qc_tool.controller import Controller
from seg_qc_tool.gui import MainWindow


def main() -> None:
    parser = argparse.ArgumentParser(description="Review medical images beside segmentation volumes.")
    parser.add_argument("--demo", action="store_true", help="Open synthetic example volumes.")
    args = parser.parse_args()
    app = QtWidgets.QApplication(sys.argv)
    with TemporaryDirectory(prefix="seg-qc-demo-") as demo_root:
        controller = Controller(persist_settings=not args.demo)
        if args.demo:
            from seg_qc_tool.demo import create_demo_dataset
            originals, segmentations = create_demo_dataset(Path(demo_root))
            controller.settings.originals_dir = originals
            controller.settings.segmentations_dir = segmentations
            controller.settings.discard_dir = Path(demo_root) / "discard"
        window = MainWindow(controller)
        window.setWindowTitle("Medical dataset reviewer" + (" · synthetic demo" if args.demo else ""))
        window.resize(1100, 680)
        window.show()
        controller.load_pairs()
        exit_code = app.exec()
        controller.executor.shutdown(wait=True)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
