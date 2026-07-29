import os
import cv2
import numpy as np
from PyQt5.QtWidgets import (
    QWidget, QPushButton, QLabel, QMainWindow, QMessageBox, 
    QVBoxLayout, QHBoxLayout, QFileDialog, QAction, QListWidget,
    QListWidgetItem, QShortcut, QSizePolicy, QSplitter, QFrame
)
from PyQt5.QtCore import Qt, QRect, QRectF, QSettings
from PyQt5.QtGui import QPixmap, QImage, QKeySequence, QColor

from gui.theme import get_theme_qss
from gui.logger import setup_logger
from libs.file_lib import FileLib
from libs.edit_lib import EditLib
from libs.view_lib import ViewLib
from libs.help_lib import HelpLib
from widgets.image_canvas import ImageCanvas
from dialog.dialog_lib import DialogLib
from dialog.select_label_dialog import SelectLabelDialog
from dialog.new_label_dialog import NewLabelDialog
from dialog.loading_dialog import LoadingDialog
from dialog.photoshop_dialog import PhotoshopDialog
from logic.auto_label_worker import AutoLabelWorker
from logic.auto_label_logic import AutoLabelLogic
from logic.auto_label_logic_v5 import AutoLabelLogicV5
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
        self.logic_v5 = AutoLabelLogicV5()

        self.labels = []
        self.label_to_id = {}
        self.current_index = 0
        self.current_images = []
        self.current_mode = None 

        self.labels_dir = None
        self.dirty = False
        self.hidden_labels = set()
        self.last_label_id = None   # nhớ class vừa chọn để tự tick sẵn cho bbox tiếp theo

        self.settings = QSettings("TPLabel", "TPLabelApp")
        self.current_theme = self.settings.value("theme", "light")

        QShortcut(QKeySequence("Ctrl+S"), self, self.save_label)
        QShortcut(QKeySequence("Ctrl+Z"), self, self.canvas.undo)
        QShortcut(QKeySequence("Ctrl+Y"), self, self.canvas.redo)
        QShortcut(QKeySequence("Ctrl+Shift+Z"), self, self.canvas.redo)

        # self.init_menu()
        self.init_ui()

    # UI
    def init_ui(self):
        self.apply_theme(self.current_theme)
        central_widget = QWidget(self)
        # status bar
        self.create_status_bar()
        self.btn_theme_toggle = QPushButton()
        self.btn_theme_toggle.setFixedWidth(110)
        self.btn_theme_toggle.setToolTip("Chuyển đổi giao diện Sáng / Tối")
        self.btn_theme_toggle.clicked.connect(self.toggle_theme)
        self._update_theme_button_text()

        status_layout = QHBoxLayout()
        status_layout.addWidget(self.model_label)
        status_layout.addStretch()
        status_layout.addWidget(self.image_info)
        status_layout.addSpacing(12)
        status_layout.addWidget(self.btn_theme_toggle)

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
        self.canvas.key_next_pressed.connect(self.next_image)
        self.canvas.key_prev_pressed.connect(self.prev_image)
        self.canvas.crosshair_pos_changed.connect(self.on_crosshair_pos_changed)

        # control buttons 
        self.btn_ok = QPushButton("📂 OK Folder")
        self.btn_ng = QPushButton("📂 NG Folder")
        self.btn_labels = QPushButton("📂 Labels Folder")
        self.btn_next = QPushButton("▶ Next Image")
        self.btn_prev = QPushButton("◀ Previous Image")
        self.btn_zoom_in = QPushButton("🔍+ Zoom In")
        self.btn_zoom_out = QPushButton("🔍− Zoom Out")
        self.btn_auto = QPushButton("⚙ Auto Labels")
        self.btn_auto_v5 = QPushButton("⚙ Auto Labels (v5)")
        self.btn_save = QPushButton("💾 Save") 
        self.btn_delete_all = QPushButton("❌ Delete") 
        self.btn_photoshop = QPushButton("🧩 Photoshop")

        # nút điều hướng/thiết lập dùng style trung tính (navBtn), không cạnh
        # tranh sự chú ý với 2 hành động quan trọng nhất (Save / Auto Labels)
        for btn in (self.btn_ok, self.btn_ng, self.btn_labels,
                    self.btn_next, self.btn_prev,
                    self.btn_zoom_in, self.btn_zoom_out, self.btn_photoshop,
                    self.btn_auto_v5):
            btn.setObjectName("navBtn")
        self.btn_save.setObjectName("successBtn")       # xanh lá - hành động an toàn
        self.btn_delete_all.setObjectName("dangerBtn")  # đỏ - hành động phá huỷ

        self.btn_ok.clicked.connect(self.select_ok_folder)
        self.btn_ng.clicked.connect(self.select_ng_folder)
        self.btn_labels.clicked.connect(self.select_labels_folder)
        self.btn_auto.clicked.connect(self.auto_label)
        self.btn_auto_v5.clicked.connect(self.auto_label_v5)
        self.btn_next.clicked.connect(self.next_image)
        self.btn_prev.clicked.connect(self.prev_image)
        self.btn_zoom_in.clicked.connect(self.canvas.zoom_in)
        self.btn_zoom_out.clicked.connect(self.canvas.zoom_out)
        self.btn_save.clicked.connect(self.save_label)
        self.btn_delete_all.clicked.connect(self.delete_curent_image_label)
        self.btn_photoshop.clicked.connect(self.open_photoshop_dialog)

        def section_title(text):
            lbl = QLabel(text)
            lbl.setObjectName("sectionTitle")
            return lbl

        def section_sep():
            line = QFrame()
            line.setObjectName("sectionSep")
            line.setFrameShape(QFrame.HLine)
            return line

        # control layout - neo trên cùng, phân nhóm rõ theo chức năng
        control_layout = QVBoxLayout()
        control_layout.setSpacing(6)

        control_layout.addWidget(section_title("THƯ MỤC"))
        control_layout.addWidget(self.btn_ok)
        control_layout.addWidget(self.btn_ng)
        control_layout.addWidget(self.btn_labels)

        control_layout.addSpacing(4)
        control_layout.addWidget(section_sep())
        control_layout.addSpacing(4)

        control_layout.addWidget(section_title("ĐIỀU HƯỚNG"))
        control_layout.addWidget(self.btn_prev)
        control_layout.addWidget(self.btn_next)

        control_layout.addSpacing(4)
        control_layout.addWidget(section_sep())
        control_layout.addSpacing(4)

        control_layout.addWidget(section_title("ZOOM"))
        control_layout.addWidget(self.btn_zoom_in)
        control_layout.addWidget(self.btn_zoom_out)

        control_layout.addSpacing(4)
        control_layout.addWidget(section_sep())
        control_layout.addSpacing(4)

        control_layout.addWidget(section_title("XỬ LÝ"))
        control_layout.addWidget(self.btn_auto)
        control_layout.addWidget(self.btn_auto_v5)
        control_layout.addWidget(self.btn_photoshop)
        control_layout.addWidget(self.btn_save)

        control_layout.addSpacing(14)   # tách xa Save - tránh bấm nhầm sang Delete
        control_layout.addWidget(self.btn_delete_all)

        control_layout.addStretch()   # đẩy toàn bộ nhóm lên trên, không canh giữa nữa

        # label list (danh sách toàn bộ class của project, có checkbox ẩn/hiện)
        self.label_list = QListWidget()
        self.label_list.itemChanged.connect(self.on_label_visibility_changed)
        self.label_list.setMinimumWidth(180)

        # box list (danh sách bbox của ảnh hiện tại, click để chọn box trên canvas)
        self.box_list = QListWidget()
        self.box_list.itemClicked.connect(self.on_box_item_clicked)
        self.box_list.setMinimumWidth(180)

        # image list 
        self.image_list = QListWidget()
        self.image_list.itemClicked.connect(self.on_image_selected)
        self.image_list.setMinimumWidth(180)

        # label panel
        label_header = QHBoxLayout()
        label_header.addWidget(QLabel("📌 Labels"))
        self.btn_toggle_all_labels = QPushButton("View")
        self.btn_toggle_all_labels.setObjectName("navBtn")
        self.btn_toggle_all_labels.setFixedWidth(50)
        self.btn_toggle_all_labels.setToolTip("Ẩn/Hiện tất cả class")
        self.btn_toggle_all_labels.clicked.connect(self.toggle_all_labels_visibility)
        label_header.addStretch()
        label_header.addWidget(self.btn_toggle_all_labels)

        label_panel = QWidget()
        label_layout = QVBoxLayout(label_panel)
        label_layout.setContentsMargins(0, 0, 0, 0)
        label_layout.addLayout(label_header)
        label_layout.addWidget(self.label_list)

        # box panel (bbox trong ảnh hiện tại)
        box_panel = QWidget()
        box_layout = QVBoxLayout(box_panel)
        box_layout.setContentsMargins(0, 0, 0, 0)
        box_layout.addWidget(QLabel("🔲 Boxes trong ảnh"))
        box_layout.addWidget(self.box_list)

        # image panel
        image_panel = QWidget()
        image_layout = QVBoxLayout(image_panel)
        image_layout.setContentsMargins(0, 0, 0, 0)
        image_layout.addWidget(QLabel("Images"))
        image_layout.addWidget(self.image_list)

        # splitter dọc - cho phép kéo giãn tỉ lệ giữa 3 khung theo nhu cầu,
        # thay vì chia đều không gian bất kể nội dung
        right_splitter = QSplitter(Qt.Vertical)
        right_splitter.addWidget(label_panel)
        right_splitter.addWidget(box_panel)
        right_splitter.addWidget(image_panel)
        right_splitter.setStretchFactor(0, 1)
        right_splitter.setStretchFactor(1, 1)
        right_splitter.setStretchFactor(2, 2)   # Images thường cần nhiều chỗ nhất
        right_splitter.setChildrenCollapsible(False)

        right_panel = QVBoxLayout()
        right_panel.setContentsMargins(0, 0, 0, 0)
        right_panel.addWidget(right_splitter)
        right_panel_widget = QWidget()
        right_panel_widget.setObjectName("rightPanel")
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
        self.refresh_image_list()
        self.statusBar().showMessage(f"Labels folder: {folder}")
        log.info(f"Select labels folder: {self.labels_dir}")

    def load_ok_folder(self, folder):
        images = self.file_lib.load_images(folder)
        if not images:
            return
        
        self.current_images = images
        self.current_index = 0
        self.refresh_image_list()
        self.current_mode = "OK"
        self.model_label.setText("MODE: OK")
        self._set_mode_badge_style("modeBadgeOK")
        self.update_image()

    def load_ng_folder(self, folder):
        images = self.file_lib.load_images(folder)
        if not images:
            return
        
        self.current_images = images
        self.current_index = 0
        self.refresh_image_list()
        self.current_mode = "NG"
        self.model_label.setText("MODE: NG")
        self._set_mode_badge_style("modeBadgeNG")
        self.update_image()

    def _set_mode_badge_style(self, object_name):
        """Đổi class QSS của badge OK/NG - dùng theme.py thay vì màu hardcode,
        nên tự đổi đúng tông khi chuyển Light/Dark."""
        self.model_label.setObjectName(object_name)
        self.model_label.style().unpolish(self.model_label)
        self.model_label.style().polish(self.model_label)

    def update_image(self):
        if not self.current_images:
            return
        image_path = self.current_images[self.current_index]
        self.canvas.load_image(image_path)
        self.load_label_file(image_path)
        self.dirty = False
        self.update_window_title()
        self.image_info.setText(f"🖼  {self.current_index + 1} / {len(self.current_images)}")
        self.image_list.blockSignals(True)
        self.image_list.setCurrentRow(self.current_index)
        self.image_list.blockSignals(False)
        log.info(f"Load image: {image_path}")

    def has_label(self, image_path):
        if not self.labels_dir:
            return False
        name = os.path.splitext(os.path.basename(image_path))[0]
        label_path = os.path.join(self.labels_dir, name + ".txt")
        return os.path.exists(label_path) and os.path.getsize(label_path) > 0

    def refresh_image_list(self):
        self.image_list.blockSignals(True)
        self.image_list.clear()
        for img in self.current_images:
            name = os.path.basename(img)
            item = QListWidgetItem(name)
            item.setData(Qt.UserRole, img)   # lưu path thật, không phụ thuộc text hiển thị
            if self.has_label(img):
                item.setText(f"✅ {name}")
                item.setForeground(QColor("#2E7D32"))   # xanh: đã gắn nhãn
            else:
                item.setText(f"⬜ {name}")
                item.setForeground(QColor("#9E9E9E"))   # xám: chưa gắn nhãn
            self.image_list.addItem(item)
        if 0 <= self.current_index < len(self.current_images):
            self.image_list.setCurrentRow(self.current_index)
        self.image_list.blockSignals(False)

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
        self.model_label.setObjectName("modeBadgeNone")
        self.model_label.setFixedHeight(30)
        self.model_label.setAlignment(Qt.AlignCenter)

        self.image_info = QLabel("🖼  0 / 0")
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
                self.refresh_label_list()

    def on_box_item_clicked(self, item):
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

    def on_label_visibility_changed(self, item):
        label_id = item.data(Qt.UserRole)
        if label_id is None:
            return
        if item.checkState() == Qt.Unchecked:
            self.hidden_labels.add(label_id)
        else:
            self.hidden_labels.discard(label_id)
        self.canvas.set_hidden_labels(self.hidden_labels)

    def on_image_selected(self, item):
        if not self.check_unsaved():
            # revert lại dòng đang chọn về đúng ảnh hiện tại (tránh lệch UI vs dữ liệu)
            self.image_list.blockSignals(True)
            self.image_list.setCurrentRow(self.current_index)
            self.image_list.blockSignals(False)
            return
        path = item.data(Qt.UserRole)
        if not path or path not in self.current_images:
            return
        self.current_index = self.current_images.index(path)
        self.update_image()
    # THEME
    def apply_theme(self, theme_name):
        self.current_theme = theme_name
        self.setStyleSheet(get_theme_qss(theme_name))
        self.settings.setValue("theme", theme_name)
        if hasattr(self, "btn_theme_toggle"):
            self._update_theme_button_text()
    def toggle_theme(self):
        new_theme = "dark" if self.current_theme == "light" else "light"
        self.apply_theme(new_theme)
    def _update_theme_button_text(self):
        if self.current_theme == "dark":
            self.btn_theme_toggle.setText("☀️ Light Mode")
        else:
            self.btn_theme_toggle.setText("🌙 Dark Mode")

    def refresh_label_list(self):
        self.label_list.blockSignals(True)
        self.label_list.clear()
        self.label_to_id.clear()
        for i, name in enumerate(self.labels):
            self.label_to_id[name] = i
            item = QListWidgetItem(name)
            item.setData(Qt.UserRole, i)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(
                Qt.Unchecked if i in self.hidden_labels else Qt.Checked
            )
            color = self.canvas.get_label_color(i)
            item.setForeground(QColor(color))
            self.label_list.addItem(item)
        self.label_list.blockSignals(False)

    def toggle_all_labels_visibility(self):
        if len(self.hidden_labels) < len(self.labels):
            self.hidden_labels = set(range(len(self.labels)))   # ẩn hết
        else:
            self.hidden_labels.clear()                          # hiện hết
        self.refresh_label_list()
        self.canvas.set_hidden_labels(self.hidden_labels)

    def refresh_box_list(self):
        self.box_list.blockSignals(True)
        self.box_list.clear()

        for idx, box in enumerate(self.canvas.boxes):
            label_id = box["label"]
            if label_id < len(self.labels):
                label_name = self.labels[label_id]
            else:
                label_name = str(label_id)

            item = QListWidgetItem(f"#{idx + 1}  {label_name}")
            item.setData(Qt.UserRole, idx)   # idx ở đây LÀ box index, dùng đúng chỗ
            color = self.canvas.get_label_color(label_id)
            item.setForeground(QColor(color))
            self.box_list.addItem(item)

        self.box_list.blockSignals(False)

    def on_box_created(self, rect:QRectF):
        dialog = SelectLabelDialog(self.labels, current=self.last_label_id, parent=self)
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
        elif action == "edit":
            idx, new_name = result
            new_name = new_name.strip()
            if new_name:
                if new_name in self.labels and self.labels[idx] != new_name:
                    QMessageBox.warning(self, "Error", "Label name already exists")
                else:
                    self._apply_label_rename(idx, new_name)
            # box vừa vẽ chưa gán nhãn nào - không thêm vào canvas, người dùng vẽ lại nếu cần
            return
        elif action == "delete":
            del_index = result
            self._apply_label_delete(del_index)
            # box vừa vẽ chưa gán nhãn nào - không thêm vào canvas, người dùng vẽ lại nếu cần
            return
        else:
            return
        self.last_label_id = label_id   # nhớ lại cho lần vẽ bbox kế tiếp
        self.canvas.boxes.append({
            "label": label_id,
            "label_name": label_name,
            "rect" : rect,
            "selected": False
        })
        self.dirty = True
        self.update_window_title()
        self.refresh_box_list()
        self.canvas.update()
        log.info(
            f"Create bbox | label={label_id}({label_name})"
            f"rect={rect.x()}, {rect.width()}, {rect.height()}"
        )

    def on_boxes_changed(self):
        self.dirty = True
        self.setWindowTitle("*" + self.windowTitle().lstrip("*"))
        self.refresh_box_list()

    def on_canvas_box_selected(self, idx):
        if idx < 0 or idx >= self.box_list.count():
            return
        self.box_list.blockSignals(True)
        self.box_list.setCurrentRow(idx)
        self.box_list.blockSignals(False)
    def on_crosshair_pos_changed(self, pos):
        """Hiển thị toạ độ X/Y ở status bar khi đang ở chế độ vẽ bbox (phím W), giống labelImg."""
        if pos is None:
            self.statusBar().clearMessage()
        else:
            self.statusBar().showMessage(f"X: {pos.x()}    Y: {pos.y()}")
    
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
        self.refresh_image_list()
        log.info(f"Save label file: {label_path}")
        log.info(f"Total boxes saved: {len(self.canvas.boxes)}")

    def delete_curent_image_label(self):
        if not self.current_images:
            return
        image_path = self.current_images[self.current_index]
        reply = QMessageBox.question(
            self,
            "Delete Image",
            f"Delete this image and its label?\n\n{image_path}",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return
        
        try:
            # delete image file
            if os.path.exists(image_path):
                os.remove(image_path)
            # delete label file
            if hasattr(self, "labels_dir") and self.labels_dir:
                name = os.path.splitext(os.path.basename(image_path))[0]
                label_path = os.path.join(self.labels_dir, name + ".txt")
                if os.path.exists(label_path):
                    os.remove(label_path)
                    log.info(f"Deleted label: {label_path}")
                else:
                    log.warning(f"Label not found: {label_path}")
            del self.current_images[self.current_index]
            # case: no images left
            if not self.current_images:
                self.canvas.pixmap = None
                self.canvas.boxes.clear()
                self.canvas.update()
                self.image_list.clear()
                self.box_list.clear()
                self.current_index = -1
                self.dirty = False
                self.update_window_title()
                self.image_info.setText("🖼  No image")
                return
            if self.current_index >= len(self.current_images):
                self.current_index = len(self.current_images) - 1
            # refresh UI list
            self.refresh_image_list()
            #load next image
            self.update_image()
            #reset dirty
            self.dirty = False
            self.update_window_title()
            log.info(f"Deleted image: {image_path}")
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to delete image: \n{str(e)}"
            )
        return
        
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
    # ---------- helper dùng chung cho rename/delete label (gọi từ cả
    # on_edit_label lẫn on_box_created, vì cả 2 đều mở SelectLabelDialog) ----------

    def _cascade_delete_label_from_files(self, del_index, skip_image_path=None):
        """Xóa/dồn id label trong TẤT CẢ file .txt trong labels_dir (trừ classes.txt
        và ảnh đang mở - ảnh đang mở xử lý qua bộ nhớ + Save như bình thường)."""
        if not self.labels_dir or not os.path.isdir(self.labels_dir):
            return
        skip_name = None
        if skip_image_path:
            skip_name = os.path.splitext(os.path.basename(skip_image_path))[0] + ".txt"

        for fname in os.listdir(self.labels_dir):
            if not fname.lower().endswith(".txt") or fname == "classes.txt":
                continue
            if fname == skip_name:
                continue
            fpath = os.path.join(self.labels_dir, fname)
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    lines = f.readlines()
            except Exception as e:
                log.warning(f"Không đọc được {fpath}: {e}")
                continue

            new_lines = []
            changed = False
            for line in lines:
                parts = line.strip().split()
                if len(parts) != 5:
                    new_lines.append(line)
                    continue
                try:
                    cls_id = int(parts[0])
                except ValueError:
                    new_lines.append(line)
                    continue
                if cls_id == del_index:
                    changed = True   # xóa hẳn dòng này
                    continue
                elif cls_id > del_index:
                    parts[0] = str(cls_id - 1)
                    new_lines.append(" ".join(parts) + "\n")
                    changed = True
                else:
                    new_lines.append(line)

            if changed:
                try:
                    with open(fpath, "w", encoding="utf-8") as f:
                        f.writelines(new_lines)
                    log.info(f"Đồng bộ xóa label id={del_index} trong {fpath}")
                except Exception as e:
                    log.warning(f"Không ghi được {fpath}: {e}")

    def _apply_label_delete(self, del_index):
        """Xóa 1 label khỏi project: cập nhật self.labels, boxes ảnh đang mở,
        classes.txt, và toàn bộ file .txt khác trong labels_dir."""
        current_image_path = None
        if 0 <= self.current_index < len(self.current_images):
            current_image_path = self.current_images[self.current_index]

        # bỏ chọn box TRƯỚC khi đụng vào set_hidden_labels/boxes - tránh IndexError
        # khi box đang chọn chính là box thuộc label vừa xóa
        self.canvas.selected_box = None

        # xóa bbox thuộc label đó trong ảnh đang mở + dồn id các box còn lại
        self.canvas.boxes = [
            b for b in self.canvas.boxes if b["label"] != del_index
        ]
        for b in self.canvas.boxes:
            if b["label"] > del_index:
                b["label"] -= 1

        self.labels.pop(del_index)

        # đồng bộ hidden_labels (id phía sau bị lùi 1)
        new_hidden = set()
        for hid in self.hidden_labels:
            if hid == del_index:
                continue
            new_hidden.add(hid - 1 if hid > del_index else hid)
        self.hidden_labels = new_hidden
        self.canvas.set_hidden_labels(self.hidden_labels)

        # đồng bộ last_label_id
        if self.last_label_id is not None:
            if self.last_label_id == del_index:
                self.last_label_id = None
            elif self.last_label_id > del_index:
                self.last_label_id -= 1

        # xóa/dồn id trong toàn bộ .txt khác + lưu classes.txt ngay lập tức
        # (đây là thay đổi cấu trúc toàn project, không đợi bấm Save)
        self._cascade_delete_label_from_files(del_index, skip_image_path=current_image_path)
        self.save_classes_file()

        self.refresh_label_list()
        self.refresh_box_list()
        self.canvas.update()

        # ảnh đang mở vẫn cần Save bình thường để ghi lại boxes đã lọc
        self.dirty = True
        self.update_window_title()

    def _apply_label_rename(self, idx, new_name):
        """Đổi tên label, GIỮ NGUYÊN vị trí/id - vì file .txt chỉ lưu id, không
        lưu tên, nên chỉ cần cập nhật classes.txt, không cần đụng file .txt nào khác."""
        self.labels[idx] = new_name
        self.refresh_label_list()
        for b in self.canvas.boxes:
            if b["label"] == idx:
                b["label_name"] = new_name
        self.save_classes_file()   # lưu ngay - đây là thay đổi cấu trúc toàn project
        self.refresh_box_list()
        self.canvas.update()
        self.dirty = True
        self.update_window_title()

    def on_edit_label(self, box_index):
        item = self.canvas.boxes[box_index]
        dialog = SelectLabelDialog(
            self.labels,
            current = item["label"],
            parent = self
        )
        if not dialog.exec_():
            return
        
        action, result = dialog.get_result()
        if action == "select":
            label_id = result
            label_name = self.labels[label_id]
            item["label"] = label_id
            item["label_name"] = label_name
            self.last_label_id = label_id
            self.dirty = True
            self.update_window_title()
        elif action == "new": 
            name = result
            if name in self.labels:
                return

            self.labels.append(name)
            self.refresh_label_list()
            label_id = len(self.labels) - 1
            item["label"] = label_id
            item["label_name"] = name
            self.last_label_id = label_id
            self.dirty = True
            self.update_window_title()
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
            self._apply_label_rename(idx, new_name)
        elif action == "delete":
            del_index = result
            self._apply_label_delete(del_index)
        self.refresh_box_list()
        self.canvas.update()
        log.info(f"Edit label on box index={box_index}")
        log.info(f"Action={action}, Result={result}")

    # load label
    def load_label_file(self, image_path):
        self.canvas.boxes.clear()
        self.refresh_box_list()
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
        self.refresh_box_list()
        self.canvas.update()

    def auto_label(self):
        self._run_auto_label(self.logic)

    def auto_label_v5(self):
        try:
            import yolov5  # noqa: F401 - chỉ để kiểm tra đã cài package chưa
        except ImportError:
            QMessageBox.warning(
                self, "Thiếu thư viện",
                "Chưa cài package 'yolov5' để chạy model YOLOv5 gốc.\n\n"
                "Cài bằng lệnh:\n    pip install yolov5"
            )
            return
        self._run_auto_label(self.logic_v5)

    def _run_auto_label(self, logic_obj):
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
        ok, conf = DialogLib.confirm(
            self,
            image_count,
            model_path,
            label_dir
        )
        if not ok:
            return

        #start worker
        self.worker = AutoLabelWorker(
            logic_obj,
            image_dir, 
            model_path,
            label_dir,
            conf
        )
        self._auto_label_cancelled = False

        #show loading (nút Hủy gọi thẳng vào worker.request_stop())
        self.loading = LoadingDialog(self, on_cancel=self._on_auto_label_cancel_requested)
        self.loading.show()

        self.worker.progress_signal.connect(self.loading.update_progress)
        self.worker.finished_signal.connect(self.on_auto_label_done)
        self.worker.error_signal.connect(self.on_auto_label_error)
        self.worker.start()

    def open_photoshop_dialog(self):
        dialog = PhotoshopDialog(self)
        dialog.exec_()

    def _on_auto_label_cancel_requested(self):
        self._auto_label_cancelled = True
        self.worker.request_stop()

    def on_auto_label_done(self, total):
        self.loading.close()
        if self._auto_label_cancelled:
            QMessageBox.information(
                self,
                "Đã hủy",
                f"⏹ Auto label đã dừng theo yêu cầu\n{total} ảnh đã xử lý xong (vẫn được giữ lại)"
            )
        else:
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
