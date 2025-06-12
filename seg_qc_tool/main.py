"""Entry point for seg_qc_tool."""

from __future__ import annotations

import sys

from PySide6 import QtWidgets

from .controller import Controller
from .gui import MainWindow


def main() -> None:
    app = QtWidgets.QApplication(sys.argv)
    controller = Controller()
    window = MainWindow(controller)
    window.show()
    controller.load_pairs()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
