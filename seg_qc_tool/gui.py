"""PySide6 GUI widgets."""

from __future__ import annotations

from pathlib import Path

from PySide6 import QtCore, QtGui, QtWidgets
from concurrent.futures import Future

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

        prev_act = QtGui.QAction("Prev", self)
        prev_act.setShortcut(QtGui.QKeySequence(QtCore.Qt.Key_Left))
        prev_act.triggered.connect(self.controller.prev_pair)
        nav.addAction(prev_act)

        next_act = QtGui.QAction("Next", self)
        next_act.setShortcut(QtGui.QKeySequence(QtCore.Qt.Key_Right))
        next_act.triggered.connect(self.controller.next_pair)
        nav.addAction(next_act)

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
        volume = self._load_volume(pair.original)
        seg = self._load_volume(pair.segmentation)
        if volume.ndim == 3:
            mid = volume.shape[0] // 2
            self.slice_slider.setMinimum(0)
            self.slice_slider.setMaximum(volume.shape[0] - 1)
            self.slice_slider.setValue(mid)
            slice_ = volume[mid]
        else:
            slice_ = volume
        self.left_view.set_image((slice_ * 255).astype('uint8'))
        if seg.ndim == 3:
            seg_slice = seg[mid]
        else:
            seg_slice = seg
        self.right_view.set_image((seg_slice * 255).astype('uint8'))

    def change_slice(self, val: int) -> None:
        if self.controller.current_index == -1:
            return
        pair = self.controller.pairs[self.controller.current_index]
        volume = self._load_volume(pair.original)
        seg = self._load_volume(pair.segmentation)
        self.left_view.set_image((volume[val] * 255).astype('uint8'))
        self.right_view.set_image((seg[val] * 255).astype('uint8'))

    def _load_volume(self, path: Path):
        future: Future = self.controller.executor.submit(load_volume, path)
        volume = future.result()
        norm, _, _ = normalize_volume(volume)
        return norm

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
