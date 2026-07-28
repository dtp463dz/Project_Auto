from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QLabel, QLineEdit, QInputDialog, QMessageBox, QFrame
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon, QPixmap, QColor, QFont


def _get_label_color(label_id):
    """Cùng công thức với ImageCanvas.get_label_color() để màu swatch trong
    dialog khớp đúng màu bbox trên canvas."""
    hue = (label_id * 47) % 360
    color = QColor()
    color.setHsv(hue, 160, 235)
    return color


def _make_swatch_icon(color, size=14):
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    from PyQt5.QtGui import QPainter, QPen
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setBrush(color)
    painter.setPen(QPen(color.darker(130), 1))
    painter.drawRoundedRect(1, 1, size - 2, size - 2, 3, 3)
    painter.end()
    return QIcon(pixmap)


class SelectLabelDialog(QDialog):
    def __init__(self, labels, current=None, parent=None):
        super().__init__(parent)
        self.labels = labels
        self.dialog_action = None
        self.dialog_data = None
        self.current = current
        self._dark = getattr(parent, "current_theme", "light") == "dark"

        self.setWindowTitle("Select Label")
        self.setMinimumSize(320, 420)

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 16, 18, 14)
        root.setSpacing(10)

        # ---------- header ----------
        title = QLabel("🏷️  Chọn Label")
        f = QFont()
        f.setPointSize(13)
        f.setBold(True)
        title.setFont(f)
        root.addWidget(title)

        # ---------- ô tìm kiếm ----------
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("🔍 Tìm label...")
        self.search_box.textChanged.connect(self._filter_list)
        root.addWidget(self.search_box)

        # ---------- danh sách label (có swatch màu khớp canvas) ----------
        self.list_widget = QListWidget()
        self.list_widget.setIconSize(QSize(14, 14))
        self._populate_list()
        self.list_widget.itemActivated.connect(self._on_item_activated)  # double-click / Enter
        root.addWidget(self.list_widget, 1)

        if current is not None and 0 <= current < len(labels):
            self.list_widget.setCurrentRow(current)

        hint = QLabel("Double-click hoặc Enter để chọn nhanh")
        hint.setObjectName("subtitle")
        root.addWidget(hint)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        root.addWidget(line)

        # ---------- hàng nút quản lý label ----------
        manage_row = QHBoxLayout()
        btn_new = QPushButton("➕ New")
        btn_edit = QPushButton("✏️ Edit")
        btn_delete = QPushButton("🗑 Delete")
        btn_new.setObjectName("navBtn")
        btn_edit.setObjectName("navBtn")
        btn_delete.setObjectName("dangerBtn")

        btn_new.clicked.connect(self.new_label)
        btn_edit.clicked.connect(self.edit_label)
        btn_delete.clicked.connect(self.delete_label)

        manage_row.addWidget(btn_new)
        manage_row.addWidget(btn_edit)
        manage_row.addWidget(btn_delete)
        root.addLayout(manage_row)

        # ---------- hàng OK / Cancel ----------
        confirm_row = QHBoxLayout()
        btn_cancel = QPushButton("Cancel")
        btn_cancel.setObjectName("navBtn")
        btn_ok = QPushButton("✓  OK")
        btn_ok.setObjectName("successBtn")
        btn_ok.setDefault(True)

        btn_cancel.clicked.connect(self.reject)
        btn_ok.clicked.connect(self.select_label)

        confirm_row.addStretch()
        confirm_row.addWidget(btn_cancel)
        confirm_row.addWidget(btn_ok)
        root.addLayout(confirm_row)

        self._apply_local_style()
        self.search_box.setFocus()

    # ---------- style ----------
    def _apply_local_style(self):
        subtitle = "#9AA3C7" if self._dark else "#6B7690"
        self.setStyleSheet(f"QLabel#subtitle {{ color: {subtitle}; font-size: 11px; }}")

    # ---------- danh sách ----------
    def _populate_list(self):
        self.list_widget.clear()
        for idx, name in enumerate(self.labels):
            item = QListWidgetItem(name)
            item.setIcon(_make_swatch_icon(_get_label_color(idx)))
            item.setData(Qt.UserRole, idx)
            self.list_widget.addItem(item)

    def _filter_list(self, text):
        text = text.strip().lower()
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            item.setHidden(text not in item.text().lower())

    def _on_item_activated(self, item):
        self.select_label()

    # ---------- actions ----------
    def new_label(self):
        text, ok = QInputDialog.getText(self, "New Label", "Label name:")
        if ok and text.strip():
            name = text.strip()
            if name in self.labels:
                QMessageBox.warning(self, "Trùng tên", f"Label '{name}' đã tồn tại.")
                return
            self.dialog_action = "new"
            self.dialog_data = name
            self.accept()

    def edit_label(self):
        row = self.list_widget.currentRow()
        if row < 0:
            QMessageBox.information(self, "Chưa chọn", "Hãy chọn 1 label để sửa.")
            return
        idx = self.list_widget.item(row).data(Qt.UserRole)
        old = self.labels[idx]
        text, ok = QInputDialog.getText(self, "Edit Label", "Label name:", text=old)
        new_name = text.strip()
        if not ok or not new_name:
            return
        if new_name in self.labels and new_name != old:
            QMessageBox.warning(self, "Duplicate label", f"Label '{new_name}' already exists.")
            return
        self.dialog_action = "edit"
        self.dialog_data = (idx, new_name)
        self.accept()

    def delete_label(self):
        row = self.list_widget.currentRow()
        if row < 0:
            QMessageBox.information(self, "Chưa chọn", "Hãy chọn 1 label để xóa.")
            return
        idx = self.list_widget.item(row).data(Qt.UserRole)
        reply = QMessageBox.question(
            self, "Delete Label",
            f"Xóa label '{self.labels[idx]}'?\n"
            f"Toàn bộ box thuộc label này (ở mọi ảnh) sẽ bị xóa theo.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.dialog_action = "delete"
            self.dialog_data = idx
            self.accept()

    def select_label(self):
        row = self.list_widget.currentRow()
        if row >= 0:
            idx = self.list_widget.item(row).data(Qt.UserRole)
            self.dialog_action = "select"
            self.dialog_data = int(idx)
            self.accept()

    def get_result(self):
        return self.dialog_action, self.dialog_data