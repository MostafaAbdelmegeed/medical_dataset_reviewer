"""PySide6 GUI widgets."""

from __future__ import annotations

from pathlib import Path

from PySide6 import QtCore, QtGui, QtWidgets
from concurrent.futures import Future
import numpy as np

from .io_utils import load_volume, normalize_volume

from .controller import Controller
from .models import Pair


class ImageView(QtWidgets.QLabel):
    """Widget that displays a grayscale slice scaled to fit."""

    def __init__(self) -> None:
        super().__init__()
        self.setAlignment(QtCore.Qt.AlignCenter)
        self._pixmap = QtGui.QPixmap()

    def set_image(self, array) -> None:
        """Set and scale an image from a numpy array."""
        h, w = array.shape
        img = QtGui.QImage(
            array.tobytes(), w, h, QtGui.QImage.Format.Format_Grayscale8
        )
        self._pixmap = QtGui.QPixmap.fromImage(img)
        self._update_pixmap()

    def resizeEvent(self, event: QtGui.QResizeEvent) -> None:  # pragma: no cover - GUI
        self._update_pixmap()
        super().resizeEvent(event)

    def _update_pixmap(self) -> None:
        if not self._pixmap.isNull():
            scaled = self._pixmap.scaled(
                self.size(),
                QtCore.Qt.AspectRatioMode.KeepAspectRatio,
                QtCore.Qt.TransformationMode.SmoothTransformation,
            )
            self.setPixmap(scaled)


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, controller: Controller) -> None:
        super().__init__()
        self.controller = controller
        self.controller.pair_changed.connect(self.load_pair)
        self.current_volume = None
        self.current_seg = None

        menubar = self.menuBar()
        file_menu = menubar.addMenu("File")
        orig_act = QtGui.QAction("Open Originals Folder…", self)
        orig_act.triggered.connect(self.choose_originals)
        file_menu.addAction(orig_act)
        seg_act = QtGui.QAction("Open Segmentations Folder…", self)
        seg_act.triggered.connect(self.choose_segmentations)
        file_menu.addAction(seg_act)
        discard_act = QtGui.QAction("Set Discard Folder…", self)
        discard_act.triggered.connect(self.choose_discard)
        file_menu.addAction(discard_act)

        self.left_view = ImageView()
        self.right_view = ImageView()

        splitter = QtWidgets.QSplitter()
        splitter.addWidget(self.left_view)
        splitter.addWidget(self.right_view)
        self.setCentralWidget(splitter)

        nav = QtWidgets.QToolBar()
        self.addToolBar(QtCore.Qt.ToolBarArea.BottomToolBarArea, nav)

        prev_btn = QtWidgets.QToolButton()
        prev_btn.setText("Prev")
        prev_btn.clicked.connect(self.controller.prev_pair)
        nav.addWidget(prev_btn)

        next_btn = QtWidgets.QToolButton()
        next_btn.setText("Next")
        next_btn.clicked.connect(self.controller.next_pair)
        nav.addWidget(next_btn)

        QtGui.QShortcut(
            QtGui.QKeySequence(QtCore.Qt.Key_Left), self
        ).activated.connect(self._dec_slice)
        QtGui.QShortcut(
            QtGui.QKeySequence(QtCore.Qt.Key_Right), self
        ).activated.connect(self._inc_slice)

        discard_btn = QtWidgets.QPushButton("Discard")
        discard_btn.setStyleSheet("background-color: red; color: white;")
        discard_btn.clicked.connect(self.discard)
        QtGui.QShortcut(QtGui.QKeySequence(QtCore.Qt.Key_D), self).activated.connect(self.discard)
        nav.addWidget(discard_btn)

        nav.addSeparator()

        self.slice_slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        nav.addWidget(self.slice_slider)
        self.slice_slider.valueChanged.connect(self.change_slice)

    def load_pair(self, pair: Pair) -> None:
        self.current_volume = None
        self.current_seg = None
        self.slice_slider.setEnabled(False)

        def loaded() -> None:
            if self.current_volume is None or self.current_seg is None:
                return
            vol = self.current_volume
            mid = vol.shape[0] // 2 if vol.ndim == 3 else 0
            self.slice_slider.setMinimum(0)
            self.slice_slider.setMaximum(vol.shape[0] - 1 if vol.ndim == 3 else 0)
            self.slice_slider.setValue(mid)
            self.controller.set_slice_index(mid)
            self._show_slice(mid)
            self.slice_slider.setEnabled(True)

        self._load_volume_async(pair.original, "current_volume", loaded)
        self._load_volume_async(pair.segmentation, "current_seg", loaded)

    def change_slice(self, val: int) -> None:
        self._show_slice(val)

    def _load_volume_async(self, path: Path, attr: str, callback) -> None:
        def worker() -> np.ndarray:
            vol = load_volume(path)
            norm, _, _ = normalize_volume(vol)
            return norm

        future: Future = self.controller.executor.submit(worker)

        def done(f: Future) -> None:
            setattr(self, attr, f.result())
            QtCore.QTimer.singleShot(0, callback)

        future.add_done_callback(done)

    def _show_slice(self, idx: int) -> None:
        if self.current_volume is None or self.current_seg is None:
            return
        self.controller.set_slice_index(idx)
        vol_slice = (
            self.current_volume[idx]
            if self.current_volume.ndim == 3
            else self.current_volume
        )
        seg_slice = (
            self.current_seg[idx] if self.current_seg.ndim == 3 else self.current_seg
        )
        self.left_view.set_image((vol_slice * 255).astype("uint8"))
        self.right_view.set_image((seg_slice * 255).astype("uint8"))

    def _dec_slice(self) -> None:
        if not self.slice_slider.isEnabled():
            return
        self.slice_slider.setValue(max(self.slice_slider.minimum(), self.slice_slider.value() - 1))

    def _inc_slice(self) -> None:
        if not self.slice_slider.isEnabled():
            return
        self.slice_slider.setValue(min(self.slice_slider.maximum(), self.slice_slider.value() + 1))

    # Actions -------------------------------------------------
    def discard(self) -> None:
        text, ok = QtWidgets.QInputDialog.getText(
            self, "Discard Comment", "Comment:", QtWidgets.QLineEdit.Normal, ""
        )
        if ok:
            self.controller.discard_current(text)

    # Folder selection ---------------------------------------
    def choose_originals(self) -> None:
        directory = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Select Originals Folder"
        )
        if directory:
            self.controller.set_originals_dir(Path(directory))

    def choose_segmentations(self) -> None:
        directory = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Select Segmentations Folder"
        )
        if directory:
            self.controller.set_segmentations_dir(Path(directory))

    def choose_discard(self) -> None:
        directory = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Select Discard Folder"
        )
        if directory:
            self.controller.set_discard_dir(Path(directory))
