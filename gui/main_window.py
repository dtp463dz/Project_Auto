import os
import cv2
import numpy as np
from PyQt5.QtWidgets import (
    QWidget, QPushButton, QLabel, QMainWindow, QMessageBox, 
    QVBoxLayout, QHBoxLayout, QFileDialog, QAction, QListWidget,
    QListWidgetItem, QShortcut, QSizePolicy
)
from PyQt5.QtCore import Qt, QRect, QRectF
from PyQt5.QtGui import QPixmap, QImage, QKeySequence

from libs.file_lib import FileLib
from libs.edit_lib import EditLib
from widgets.image_canvas import ImageCanvas
from libs.view_lib import ViewLib
from libs.help_lib import HelpLib
from dialog.dialog_lib import DialogLib
from dialog.select_label_dialog import SelectLabelDialog
from logic.auto_label_logic import AutoLabelLogic
from dialog.new_label_dialog import NewLabelDialog
from gui.logger import setup_logger
from logic.auto_label_worker import AutoLabelWorker
from dialog.loading_dialog import LoadingDialog
log = setup_logger()

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

        self.labels_dir = None
        self.dirty = False
        QShortcut(QKeySequence("Ctrl+S"), self, self.save_label)

        # self.init_menu()
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
        self.canvas.setSizePolicy(
            QSizePolicy.Expanding, 
            QSizePolicy.Expanding
        )
        self.canvas.box_created.connect(self.on_box_created)
        self.canvas.box_created.connect(self.on_boxes_changed)
        self.canvas.boxes_changed.connect(self.on_boxes_changed)
        self.canvas.box_selected.connect(self.on_canvas_box_selected)
        self.canvas.box_double_clicked.connect(self.on_edit_label)

        # control buttons 
        self.btn_ok = QPushButton("📂 OK Folder")
        self.btn_ng = QPushButton("📂 NG Folder")
        self.btn_labels = QPushButton("📂 Labels Folder")
        self.btn_next = QPushButton("Next Image")
        self.btn_prev = QPushButton("Previous Image")
        self.btn_zoom_in = QPushButton("Zoom In")
        self.btn_zoom_out = QPushButton("Zoom Out")
        self.btn_auto = QPushButton("⚙ Auto Labels")
        self.btn_save = QPushButton("💾 Save")

        self.btn_ok.clicked.connect(self.select_ok_folder)
        self.btn_ng.clicked.connect(self.select_ng_folder)
        self.btn_labels.clicked.connect(self.select_labels_folder)
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
        control_layout.addWidget(self.btn_labels)
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
        right_panel_widget = QWidget()
        right_panel_widget.setLayout(right_panel)
        right_panel_widget.setFixedWidth(220)

        # main layout 
        main_layout = QHBoxLayout()
        main_layout.addLayout(control_layout)
        main_layout.addWidget(self.canvas)
        main_layout.addWidget(right_panel_widget)

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

        self.actionUndo.triggered.connect(self.canvas.undo)
        self.actionRedo.triggered.connect(self.canvas.redo)

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
        if not folder:
            return
        if not self.check_unsaved():
            return
        if folder:
            self.load_ok_folder(folder)
            log.info(f"Select OK images folder: {folder}")
            log.info(f"Total images loaded: {len(self.current_images)}")
            self.dirty = False
            self.update_window_title()

    def select_ng_folder(self): 
        folder = QFileDialog.getExistingDirectory(self, "Select NG Folder")
        if not folder:
            return
        if not self.check_unsaved():
            return
        if folder:
            self.load_ng_folder(folder)
            log.info(f"Select NG images folder: {folder}")
            log.info(f"Total images loaded: {len(self.current_images)}")
            self.dirty = False
            self.update_window_title()

    def select_labels_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Labels Folder")
        if not folder:
            return
        self.labels_dir = folder
        self.load_classes_file()
        self.statusBar().showMessage(f"Labels folder: {folder}")
        log.info(f"Select labels folder: {self.labels_dir}")

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
        image_path = self.current_images[self.current_index]
        self.canvas.load_image(image_path)
        self.load_label_file(image_path)
        self.dirty = False
        self.update_window_title()
        self.image_info.setText(f"{self.current_index + 1} / {len(self.current_images)}")
        self.image_list.blockSignals(True)
        self.image_list.setCurrentRow(self.current_index)
        self.image_list.blockSignals(False)
        log.info(f"Load image: {image_path}")

    def update_window_title(self):
        if not self.current_images:
            self.setWindowTitle("Label Tool")
            return
        image_name = os.path.basename(
            self.current_images[self.current_index]
        )
        if self.dirty:
            title = f"{image_name} *"
        else:
            title = image_name
        self.setWindowTitle(title)

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
        if not self.check_unsaved():
            return
        if self.current_index < len(self.current_images) - 1:
            self.current_index += 1
            self.update_image()

    def prev_image(self):
        
        if not self.current_images:
            print('prev fail')
            return
        if not self.check_unsaved():
            return
        if self.current_index > 0:
            self.current_index -= 1
            self.update_image()

    def create_label(self):
        dialog = NewLabelDialog()
        if dialog.exec_(): 
            name = dialog.name.strip()
            if not name:
                return
            if name not in self.label_to_id:
                label_id = len(self.labels)
                self.labels.append(name)
                self.label_to_id[name] = label_id
                # self.label_list.addItem(name)
                self.refresh_label_list()

    def on_label_selected(self, item):
        bbox_index = item.data(Qt.UserRole)
        if bbox_index is None:
            return
        if bbox_index >= len(self.canvas.boxes):
            return
        
        self.canvas.selected_box = bbox_index
        label_id = self.canvas.boxes[bbox_index]["label"]
        self.canvas.current_label = label_id
        self.canvas.set_label_cursor(label_id)
        self.canvas.update()
        print("Selected from list: ", bbox_index)

    def on_image_selected(self, item):
        if not self.check_unsaved():
            return
        name = item.text()
        for i, path in enumerate(self.current_images):
            if os.path.basename(path) == name:
                self.current_index = i
                self.update_image()
                self.load_label_file(path)
                break

    def refresh_label_list(self):
        self.label_list.blockSignals(True)
        self.label_list.clear()
        self.label_to_id.clear()
        for idx, name in enumerate(self.labels):
            self.label_list.addItem(name)
            self.label_to_id[name] = idx 
        self.label_list.blockSignals(False)

    def refresh_label_list_from_boxes(self): 
        self.label_list.blockSignals(True)
        self.label_list.clear()

        for idx, box in enumerate(self.canvas.boxes):
            label_id = box["label"]
            if label_id < len(self.labels):
                label_name = self.labels[label_id]
            else:
                label_name = str(label_id)

            item = QListWidgetItem(label_name)
            item.setData(Qt.UserRole, idx)
            self.label_list.addItem(item)

        self.label_list.blockSignals(False)
        

    def on_box_created(self, rect:QRectF):
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
                self.refresh_label_list()
            label_id = self.labels.index(label_name)
        else:
            return
        self.canvas.boxes.append({
            "label": label_id,
            "label_name": label_name,
            "rect" : rect,
            "selected": False
        })
        self.dirty = True
        self.update_window_title()
        self.canvas.update()
        log.info(
            f"Create bbox | label={label_id}({label_name})"
            f"rect={rect.x()}, {rect.width()}, {rect.height()}"
        )

    def on_boxes_changed(self):
        self.dirty = True
        self.setWindowTitle("*" + self.windowTitle().lstrip("*"))

    def on_canvas_box_selected(self, idx):
        if idx < 0 or idx >= self.label_list.count():
            return
        self.label_list.blockSignals(True)
        self.label_list.setCurrentRow(idx)
        self.label_list.blockSignals(False)
       
    
    def check_unsaved(self):
        if not self.dirty:
            return True
        
        reply = QMessageBox.question(
            self, 
            "Unsaved Changes",
            "Save changes to current image?",
            QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel, 
            QMessageBox.Yes
        )

        if reply == QMessageBox.Yes:
            self.save_label()
            self.dirty = False
            return True
        elif reply == QMessageBox.No:
            self.dirty = False
            self.update_window_title()
            return True
        else:
            return False

    def save_label(self):
        if not self.labels_dir:
            QMessageBox.warning(
                self,
                "No Labels Folder",
                "Please select Labels Folder first"
            )
            return
        if not self.canvas.pixmap:
            return

        h = self.canvas.pixmap.height()
        w = self.canvas.pixmap.width()
        image_path = self.current_images[self.current_index]
        image_name = os.path.splitext(os.path.basename(image_path))[0]
        label_path = os.path.join(self.labels_dir, image_name + ".txt")

        with open(label_path, "w") as f:
            for item in self.canvas.boxes:
                label = int(item["label"])
                box = item["rect"]

                x = (box.center().x()) / w
                y = (box.center().y()) / h
                bw = box.width() / w
                bh = box.height() / h
                f.write(f"{label} {x:.6f} {y:.6f} {bw:.6f} {bh:.6f}\n")
        self.save_classes_file()
        self.dirty = False
        self.update_window_title()
        log.info(f"Save label file: {label_path}")
        log.info(f"Total boxes saved: {len(self.canvas.boxes)}")

        
    def save_classes_file(self):
        if not self.labels_dir:
            return
        path = os.path.join(self.labels_dir, "classes.txt")
        with open(path, "w", encoding="utf-8") as f:
            for name in self.labels:
                f.write(name + "\n")
        log.info(f"Saved classes file: {path}")

    def load_classes_file(self):
        classes_path = os.path.join(self.labels_dir, "classes.txt")
        if not os.path.exists(classes_path):
            log.info("classes.txt not found, start with empty labels")
            return
        with open(classes_path, "r", encoding="utf-8") as f:
            self.labels = [line.strip() for line in f if line.strip()]
        log.info(f"Load classes file: {classes_path}")
        log.info(f"Classes: {self.labels}")
        self.refresh_label_list()

    def load_predefined_classes(self):
        path = os.path.join(self.labels_dir, "data", "predefined_classes.txt")
        if not os.path.exists(path):
            return
        with open(path, "r", encoding="utf-8") as f:
            self.labels = [line.strip() for line in f if line.strip()]
        self.refresh_label_list() 

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
            new_name = new_name.strip()
            if not new_name:
                return
            # check trùng tên label
            if new_name in self.labels and self.labels[idx] != new_name:
                QMessageBox.warning(self, "Error", "Label name already exists")
                return
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
        log.info(f"Edit label on box index={box_index}")
        log.info(f"Action={action}, Result={result}")


    # load label
    def load_label_file(self, image_path):
        self.canvas.boxes.clear()

        if not self.labels_dir or not self.canvas.pixmap:
            return
        image_name = os.path.splitext(os.path.basename(image_path))[0]
        label_path = os.path.join(self.labels_dir, image_name + ".txt")

        if not os.path.exists(label_path):
            self.canvas.update()
            return
        h = self.canvas.pixmap.height()
        w = self.canvas.pixmap.width()

        with open(label_path, "r") as f:
            for line in f: 
                parts = line.strip().split()
                if len(parts) != 5:
                    continue
                label_id = int(parts[0])
                x, y, bw, bh = map(float, parts[1:])

                cx = x * w
                cy = y * h
                rw = bw * w
                rh = bh * h

                rect = QRect(
                    int(cx - rw / 2),
                    int(cy - rh / 2),
                    int(rw),
                    int(rh)
                )

                label_name = (
                    self.labels[label_id]
                    if label_id < len(self.labels)
                    else str(label_id)
                )

                self.canvas.boxes.append({
                    "label": label_id,
                    "label_name": label_name,
                    "rect": rect,
                    "selected": False
                })
        self.refresh_label_list_from_boxes()
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

        #show loading
        self.loading = LoadingDialog(self)
        self.loading.show()
        #start worker
        self.worker = AutoLabelWorker(
            self.logic,
            image_dir, 
            model_path,
            label_dir
        )
        self.worker.finished_signal.connect(self.on_auto_label_done)
        self.worker.error_signal.connect(self.on_auto_label_error)
        self.worker.start()

    def on_auto_label_done(self, total):
        self.loading.close()
        QMessageBox.information(
            self,
            "Done",
            f"✅ Auto label hoàn tất\n{total} ảnh"
        )

    def on_auto_label_error(self, error):
        self.loading.close()
        QMessageBox.critical(
            self,
            "Error",
            error
        )