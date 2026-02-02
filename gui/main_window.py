import os
import cv2
import numpy as np
from PyQt5.QtWidgets import (
    QWidget, QPushButton, QLabel, QMainWindow, QMessageBox,
    QVBoxLayout, QHBoxLayout, QFileDialog, QAction, QListWidget
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QImage

from libs.file_lib import FileLib
from libs.edit_lib import EditLib
from widgets.image_canvas import ImageCanvas
from libs.view_lib import ViewLib
from libs.help_lib import HelpLib
from dialog.dialog_lib import DialogLib
from dialog.select_label_dialog import SelectLabelDialog
from logic.auto_label_logic import AutoLabelLogic
from dialog.new_label_dialog import NewLabelDialog


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TPLabel")
        self.resize(1200, 700)
        self.file_lib = FileLib(self)
        self.edit_lib = EditLib(self)
        self.view_lib = ViewLib(self)
        self.help_lib = HelpLib(self)
        self.canvas = ImageCanvas()
        self.logic = AutoLabelLogic()

        self.labels = []
        self.label_to_id = {}
        self.current_index = 0
        self.current_images = []
        self.current_mode = None 

        self.init_menu()
        self.init_ui()

    # UI
    def init_ui(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #F7F9FC;
                font-family: Segoe UI;
                font-size: 13px;
            }

            QPushButton {
                background-color: #4A90E2;
                color: white;
                border-radius: 6px;
                padding: 6px 14px;
            }
                           
            QPushButton:hover {
                background-color: #6AAEFF;
            }

            QPushButton:pressed {
                background-color: #357ABD;
            }
           
            """)
        central_widget = QWidget(self)
        # status bar
        self.create_status_bar()
        status_layout = QHBoxLayout()
        status_layout.addWidget(self.model_label)
        status_layout.addStretch()
        status_layout.addWidget(self.image_info)

        # canvas
        self.canvas.setMinimumSize(800, 600)
        self.canvas.box_created.connect(self.on_box_created)
        self.canvas.box_double_clicked.connect(self.on_edit_label)

        # control buttons 
        self.btn_ok = QPushButton("📂 OK Folder")
        self.btn_ng = QPushButton("📂 NG Folder")
        self.btn_next = QPushButton("Next Image")
        self.btn_prev = QPushButton("Previous Image")
        self.btn_zoom_in = QPushButton("Zoom In")
        self.btn_zoom_out = QPushButton("Zoom Out")
        self.btn_auto = QPushButton("⚙ Auto Labels")
        self.btn_save = QPushButton("💾 Save")

        self.btn_ok.clicked.connect(self.select_ok_folder)
        self.btn_ng.clicked.connect(self.select_ng_folder)
        self.btn_auto.clicked.connect(self.auto_label)
        self.btn_next.clicked.connect(self.next_image)
        self.btn_prev.clicked.connect(self.prev_image)
        self.btn_zoom_in.clicked.connect(self.canvas.zoom_in)
        self.btn_zoom_out.clicked.connect(self.canvas.zoom_out)
        self.btn_save.clicked.connect(self.save_label)

        # control layout
        control_layout = QVBoxLayout()
        control_layout.addStretch()
        control_layout.addWidget(self.btn_ok)
        control_layout.addWidget(self.btn_ng)
        control_layout.addWidget(self.btn_auto)
        control_layout.addWidget(self.btn_next)
        control_layout.addWidget(self.btn_prev)
        control_layout.addWidget(self.btn_zoom_in)
        control_layout.addWidget(self.btn_zoom_out)
        control_layout.addWidget(self.btn_save)
        control_layout.addStretch()

        # label list 
        self.label_list = QListWidget()
        self.label_list.itemClicked.connect(self.on_label_selected)
        # image list 
        self.image_list = QListWidget()
        self.image_list.itemClicked.connect(self.on_image_selected)
        
        self.label_list.setMinimumWidth(180)
        self.image_list.setMinimumWidth(180)

        # label layout
        label_layout = QVBoxLayout()
        label_layout.addWidget(QLabel("📌 Labels"))
        label_layout.addWidget(self.label_list)
        #image layout
        image_layout = QVBoxLayout()
        image_layout.addWidget(QLabel("Images"))
        image_layout.addWidget(self.image_list)

        right_panel = QVBoxLayout()
        right_panel.addLayout(label_layout)
        right_panel.addLayout(image_layout)

        # main layout 
        main_layout = QHBoxLayout()
        main_layout.addLayout(control_layout)
        main_layout.addWidget(self.canvas)
        main_layout.addLayout(right_panel)

        root_layout = QVBoxLayout()
        root_layout.addLayout(status_layout)
        root_layout.addLayout(main_layout)

        central_widget.setLayout(root_layout)
        self.setCentralWidget(central_widget)
        self.refresh_label_list()

    # MENU 
    def init_menu(self):
        menubar = self.menuBar()

        file_menu = menubar.addMenu("File")

        open_ok = QAction("Open OK Folder", self)
        open_ng = QAction("Open NG Folder", self)
        exit_app = QAction("Exit", self)

        open_ok.triggered.connect(self.select_ok_folder)
        open_ng.triggered.connect(self.select_ng_folder)
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

    def select_ok_folder(self): 
        folder = QFileDialog.getExistingDirectory(self, "Select OK Folder")
        if folder:
            self.load_ok_folder(folder)

    def select_ng_folder(self): 
        folder = QFileDialog.getExistingDirectory(self, "Select NG Folder")
        if folder:
            self.load_ng_folder(folder)

    def load_ok_folder(self, folder):
        images = self.file_lib.load_images(folder)
        if not images:
            return
        
        self.current_images = images
        self.image_list.clear()
        for img in images:
            self.image_list.addItem(os.path.basename(img))
        self.current_index = 0
        self.current_mode = "OK"
        self.model_label.setText("MODE: OK")
        self.model_label.setStyleSheet("""
            QLabel {
                background-color: #E8F5E9;
                border: 1px solid #81C784;
                color: #2E7D32;
                font-size: 16px;
                font-weight: bold;
            }
        """)
        self.update_image()

    def load_ng_folder(self, folder):
        images = self.file_lib.load_images(folder)
        if not images:
            return
        
        self.current_images = images
        self.current_index = 0
        self.current_mode = "NG"
        self.model_label.setText("MODE: NG")
        self.model_label.setStyleSheet("""
            QLabel {
                background-color: #FDECEA;
                border: 1px solid #EF9A9A;
                color: #B71C1C;
                font-size: 16px;
                font-weight: bold;
            }
        """)
        self.update_image()

    def update_image(self):
        if not self.current_images:
            return
        self.canvas.load_image(self.current_images[self.current_index])
        self.image_info.setText(f"{self.current_index + 1} / {len(self.current_images)}")
        self.image_list.setCurrentRow(self.current_index)

    def create_status_bar(self): 
        self.model_label = QLabel("MODE: NONE")
        self.model_label.setFixedHeight(36)
        self.model_label.setAlignment(Qt.AlignCenter)
        self.model_label.setStyleSheet("""
            QLabel {
                background-color: #E3F2FD;
                border: 1px solid #90CAF9;
                border-radius: 6px;
                font-size: 16px;
                font-weight: bold;
                color: #1565C0;
            }
        """)

        self.image_info = QLabel("0 / 0")
        self.image_info.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

    def next_image(self):
        if not self.current_images:
            print('next fail')
            return
        if self.current_index < len(self.current_images) - 1:
            self.current_index += 1
            self.canvas.load_image(self.current_images[self.current_index])

    def prev_image(self):
        if not self.current_images:
            print('prev fail')
            return
        if self.current_index > 0:
            self.current_index -= 1
            self.canvas.load_image(self.current_images[self.current_index])

    def create_label(self):
        dialog = NewLabelDialog()
        if dialog.exec_(): 
            name = dialog.name
            if name not in self.label_to_id:
                label_id = len(self.labels)
                self.labels.append(name)
                self.label_to_id[name] = label_id
                self.label_list.addItem(name)

    def on_label_selected(self, item):
        label_name = item.text()
        label_id = self.label_to_id[label_name]                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          
        self.canvas.set_label(label_id)

    def on_image_selected(self, item):
        name = item.text()
        for i, path in enumerate(self.current_images):
            if os.path.basename(path) == name:
                self.current_index = i
                self.update_image()
                break

    def refresh_label_list(self):
        self.label_list.clear()
        for name in self.labels:
            self.label_list.addItem(str(name))

    def on_box_created(self, rect):
        dialog = SelectLabelDialog(self.labels)
        if not dialog.exec_():
            return
        action, result = dialog.get_result()
        if action == "select":
            if not isinstance(result, int):
                print("BUG: select nhưng result = ", result, type(result))
                return
            label_id = result
            label_name = self.labels[label_id]
        elif action == "new":
            label_name = result
            if label_name not in self.labels:
                self.labels.append(label_name)
            label_id = self.labels.index(label_name)
        else:
            return
        self.canvas.boxes.append({
            "label": label_id,
            "label_name": label_name,
            "rect" : rect,
            "selected": False
        })
        self.canvas.update()

    def save_label(self):
        h = self.canvas.pixmap.height()
        w = self.canvas.pixmap.width()
        label_path = self.current_images[self.current_index]
        label_path = label_path.replace("images", "labels").replace(".jpg", ".txt")

        with open(label_path, "w") as f:
            for item in self.canvas.boxes:
                label = item["label"]
                box = item["rect"]

                x = (box.center().x()) / w
                y = (box.center().y()) / h
                bw = box.width() / w
                bh = box.height() / h
                f.write(f"{label} {x:.6f} {y:.6f} {bw:.6f} {bh:.6f}\n")

    # edit label
    def on_edit_label(self, box_index):
        item = self.canvas.boxes[box_index]
        dialog = SelectLabelDialog(
            self.labels,
            current = item["label"]
        )
        if not dialog.exec_():
            return
        
        action, result = dialog.get_result()
        if action == "select":
            label_id = result
            label_name = self.labels[label_id]
            item["label"] = label_id
            item["label_name"] = label_name
        elif action == "new": 
            name = result
            if name in self.labels:
                return

            self.labels.append(name)
            self.refresh_label_list()
            label_id = len(self.labels) - 1
            item["label"] = label_id
            item["label_name"] = name
            self.canvas.update()
        elif action == "edit":
            idx, new_name = result
            self.labels[idx] = new_name
            self.refresh_label_list()
            # update tất cả bbox dùng label đó
            for b in self.canvas.boxes:
                if b["label"] == idx:
                    b["label_name"] = new_name
        elif action == "delete":
            del_index = result
            # xóa bbox thuộc label đó
            self.canvas.boxes = [
                b for b in self.canvas.boxes
                if b["label"] != del_index
            ]

            # update label id phía sau
            for b in self.canvas.boxes:
                if b["label"] > del_index:
                    b["label"] -= 1
            self.labels.pop(del_index)
            self.refresh_label_list()
            self.canvas.selected_box = None
        self.canvas.update()

    def auto_label(self):
        image_dir = DialogLib.select_image_folder(self)
        if not image_dir:
            return
        model_path = DialogLib.select_model_file(self)
        if not model_path:
            return
        label_dir = DialogLib.select_label_folder(self)
        if not label_dir:
            return
        image_count = len([
            f for f in os.listdir(image_dir)
            if f.lower().endswith((".jpg", ".png", ".jpeg"))
        ])
        ok = DialogLib.confirm(
            self,
            image_count,
            model_path,
            label_dir
        )
        if not ok:
            return
        total = self.logic.run(
            image_dir=image_dir,
            model_path=model_path,
            label_dir=label_dir
        )
        QMessageBox.information(
            self,
            "Done",
            f"✅ Auto label hoàn tất\n{total} ảnh"
        )