"""Entry point for seg_qc_tool."""

from __future__ import annotations

import sys
from pathlib import Path

# Allow running this file directly without installing the package
if __package__ is None:  # pragma: no cover - simple path fix
    sys.path.append(str(Path(__file__).resolve().parent.parent))

from PySide6 import QtWidgets

# Use absolute imports so running this file directly works too
from seg_qc_tool.controller import Controller
from seg_qc_tool.gui import MainWindow


def main() -> None:
    app = QtWidgets.QApplication(sys.argv)
    controller = Controller()
    window = MainWindow(controller)
    window.show()
    controller.load_pairs()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
