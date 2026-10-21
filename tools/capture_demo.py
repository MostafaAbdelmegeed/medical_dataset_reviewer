"""Capture the actual reviewer with synthetic example volumes."""

from pathlib import Path
import sys
import os
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6 import QtWidgets, QtGui
from seg_qc_tool.controller import Controller
from seg_qc_tool.demo import create_demo_dataset
from seg_qc_tool.gui import MainWindow


def main():
    app = QtWidgets.QApplication([])
    app.setStyle("Fusion")
    if sys.platform == "win32":
        font_file = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts" / "segoeui.ttf"
        if font_file.exists():
            font_id = QtGui.QFontDatabase.addApplicationFont(str(font_file))
            families = QtGui.QFontDatabase.applicationFontFamilies(font_id)
            if families:
                app.setFont(QtGui.QFont(families[0], 10))
    with TemporaryDirectory(prefix="reviewer-preview-") as root:
        controller = Controller(persist_settings=False)
        originals, segmentations = create_demo_dataset(Path(root))
        controller.settings.originals_dir = originals
        controller.settings.segmentations_dir = segmentations
        window = MainWindow(controller)
        window.setWindowTitle("Medical dataset reviewer · synthetic demo")
        window.resize(1100, 680)
        window.show()
        controller.load_pairs()
        app.processEvents()
        assert len(controller.pairs) == 2
        assert not window.left_view.pixmap().isNull()
        assert not window.right_view.pixmap().isNull()
        assert window.slice_slider.maximum() == 47
        window.slice_slider.setValue(28)
        app.processEvents()
        assert controller.current_slice == 28
        destination = Path(__file__).resolve().parents[1] / "resources" / "demo.png"
        destination.parent.mkdir(exist_ok=True)
        assert window.grab().save(str(destination))
        controller.next_pair()
        app.processEvents()
        assert controller.current_index == 1
        assert not window.right_view.pixmap().isNull()
        controller.prev_pair()
        app.processEvents()
        assert controller.current_index == 0
        window.close()
        controller.executor.shutdown(wait=True)
        print(f"Captured {destination.name}; slice review and pair navigation passed.")


if __name__ == "__main__":
    main()
