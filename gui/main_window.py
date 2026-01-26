import os
import cv2
from PyQt5.QtWidgets import (
    QWidget, QPushButton, QLabel, QMainWindow,
    QVBoxLayout, QHBoxLayout, QFileDialog, QAction
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QImage

from libs.file_lib import FileLib
from libs.edit_lib import EditLib
from libs.view_lib import ViewLib
from libs.help_lib import HelpLib

from logic.auto_label_logic import AutoLabelLogic
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("TPLabel")
        self.resize(1200, 700)
        self.file_lib = FileLib(self)
        self.edit_lib = EditLib(self)
        self.view_lib = ViewLib(self)
        self.help_lib = HelpLib(self)
        self.logic = AutoLabelLogic()

        self.ok_images = []
        self.ng_images = []
        self.save_images = []

        self.init_menu()
        self.init_ui()

    # UI
    def init_ui(self):
        central_widget = QWidget(self)
        self.btn_ok = QPushButton("📂 OK Folder")
        self.btn_ng = QPushButton("📂 NG Folder")
        self.btn_auto = QPushButton("⚙ Auto Labels")
        self.btn_saveImg = QPushButton("💾 Save Images")

        self.btn_ok.clicked.connect(self.open_ok_folder)
        self.btn_ng.clicked.connect(self.open_ng_folder)
        self.btn_auto.clicked.connect(self.auto_label)
        # self.btn_saveImg.clicked.connect(self.save_images)
        left_layout = QVBoxLayout()
        left_layout.addWidget(self.btn_ok)
        left_layout.addWidget(self.btn_ng)
        left_layout.addWidget(self.btn_auto)
        left_layout.addWidget(self.btn_saveImg)
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

        central_widget.setLayout(main_layout)

        self.setCentralWidget(central_widget)

    # MENU 
    def init_menu(self):
        menubar = self.menuBar()

        file_menu = menubar.addMenu("File")

        open_ok = QAction("Open OK Folder", self)
        open_ng = QAction("Open NG Folder", self)
        exit_app = QAction("Exit", self)

        open_ok.triggered.connect(self.open_ok_folder)
        open_ng.triggered.connect(self.open_ng_folder)
        exit_app.triggered.connect(self.close)

        file_menu.addAction(open_ok)
        file_menu.addAction(open_ng)
        file_menu.addSeparator()
        file_menu.addAction(exit_app)

        edit_menu = menubar.addMenu("Edit")

        undo = QAction("Undo", self)
        redo = QAction("Redo", self)

        undo.triggered.connect(self.edit_lib.undo)
        redo.triggered.connect(self.edit_lib.redo)

        edit_menu.addAction(undo)
        edit_menu.addAction(redo)

        view_menu = menubar.addMenu("View")

        zoom_in = QAction("Zoom In", self)
        zoom_out = QAction("Zoom Out", self)
        reset = QAction("Reset View", self)

        zoom_in.triggered.connect(self.view_lib.zoom_in)
        zoom_out.triggered.connect(self.view_lib.zoom_out)

        view_menu.addAction(zoom_in)
        view_menu.addAction(zoom_out)
        view_menu.addSeparator()
        view_menu.addAction(reset)

        help_menu = menubar.addMenu("Help")

        about = QAction("About TPLabel", self)
        about.triggered.connect(self.help_lib.show_about)

        help_menu.addAction(about)

    def open_ok_folder(self):
        folder = self.file_lib.open_ok_menu()
        if folder:
            self.ok_images = self.file_lib.load_images(folder)
            if self.ok_images:
                self.show_image(self.ok_images[0], self.ok_label)

    def open_ng_folder(self):
        folder = self.file_lib.open_ng_menu()
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

    def save_images(self): 
        print("Save images implementations")
