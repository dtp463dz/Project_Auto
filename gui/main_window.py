import os
import cv2
from PyQt5.QtWidgets import (
    QWidget, QPushButton, QLabel,
    QVBoxLayout, QHBoxLayout, QFileDialog
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QImage

from libs.file_lib import FileLib
from logic.auto_label_logic import AutoLabelLogic


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("TPLabel")
        self.setGeometry(200, 100, 1200, 700)

        self.file_lib = FileLib()
        self.logic = AutoLabelLogic()

        self.ok_images = []
        self.ng_images = []

        self.init_ui()

    def init_ui(self):
        self.btn_ok = QPushButton("📂 OK Folder")
        self.btn_ng = QPushButton("📂 NG Folder")
        self.btn_auto = QPushButton("⚙ Auto Labels")

        self.btn_ok.clicked.connect(self.open_ok_folder)
        self.btn_ng.clicked.connect(self.open_ng_folder)
        self.btn_auto.clicked.connect(self.auto_label)

        left_layout = QVBoxLayout()
        left_layout.addWidget(self.btn_ok)
        left_layout.addWidget(self.btn_ng)
        left_layout.addWidget(self.btn_auto)
        left_layout.addStretch()

        self.ok_label = QLabel("OK IMAGE")
        self.ng_label = QLabel("NG IMAGE")

        self.ok_label.setAlignment(Qt.AlignCenter)
        self.ng_label.setAlignment(Qt.AlignCenter)
        self.ok_label.setStyleSheet("border:2px solid green;")
        self.ng_label.setStyleSheet("border:2px solid red;")
        self.ok_label.setFixedSize(500, 500)
        self.ng_label.setFixedSize(500, 500)

        image_layout = QHBoxLayout()
        image_layout.addWidget(self.ok_label)
        image_layout.addWidget(self.ng_label)

        main_layout = QHBoxLayout()
        main_layout.addLayout(left_layout)
        main_layout.addLayout(image_layout)

        self.setLayout(main_layout)

    def open_ok_folder(self):
        folder = self.file_lib.open_folder(self)
        if folder:
            self.ok_images = self.file_lib.load_images(folder)
            if self.ok_images:
                self.show_image(self.ok_images[0], self.ok_label)

    def open_ng_folder(self):
        folder = self.file_lib.open_folder(self)
        if folder:
            self.ng_images = self.file_lib.load_images(folder)
            if self.ng_images:
                self.show_image(self.ng_images[0], self.ng_label)

    def auto_label(self):
        self.logic.run(self.ok_images, self.ng_images)

    def show_image(self, path, label):
        img = cv2.imread(path)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        h, w, ch = img.shape
        qt_img = QImage(img.data, w, h, ch*w, QImage.Format_RGB888)
        pix = QPixmap.fromImage(qt_img)
        pix = pix.scaled(label.width(), label.height(), Qt.KeepAspectRatio)
        label.setPixmap(pix)
