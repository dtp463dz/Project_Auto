from PyQt5.QtWidgets import (
    QDialog, QLabel, QVBoxLayout, QHBoxLayout, QProgressBar, QPushButton
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont


class LoadingDialog(QDialog):

    def __init__(self, parent=None, on_cancel=None):
        super().__init__(parent)
        self._dark = getattr(parent, "current_theme", "light") == "dark"
        self._on_cancel = on_cancel
        self._cancel_requested = False

        self.setWindowTitle("Auto Label")
        self.setModal(True)
        self.setFixedSize(380, 150)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowCloseButtonHint)
        self._apply_local_style()

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 18, 20, 16)
        root.setSpacing(10)

        title = QLabel("🤖  Đang chạy Auto Label...")
        f = QFont()
        f.setPointSize(12)
        f.setBold(True)
        title.setFont(f)
        root.addWidget(title)

        self.file_label = QLabel("Đang chuẩn bị...")
        self.file_label.setObjectName("subtitle")
        self.file_label.setWordWrap(True)
        root.addWidget(self.file_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%p%")
        root.addWidget(self.progress_bar)

        bottom_row = QHBoxLayout()
        self.count_label = QLabel("0 / 0")
        self.count_label.setObjectName("subtitle")
        bottom_row.addWidget(self.count_label)
        bottom_row.addStretch()

        self.btn_cancel = QPushButton("Hủy")
        self.btn_cancel.setObjectName("secondaryBtn")
        self.btn_cancel.setFixedWidth(90)
        self.btn_cancel.clicked.connect(self._handle_cancel_clicked)
        bottom_row.addWidget(self.btn_cancel)

        root.addLayout(bottom_row)

    def update_progress(self, done, total, filename):
        if total <= 0:
            return
        percent = int(done / total * 100)
        self.progress_bar.setValue(percent)
        self.count_label.setText(f"{done} / {total}")
        self.file_label.setText(f"Đang xử lý: {filename}")

    def _handle_cancel_clicked(self):
        if self._cancel_requested:
            return
        self._cancel_requested = True
        self.btn_cancel.setEnabled(False)
        self.btn_cancel.setText("Đang dừng...")
        self.file_label.setText("Đang dừng - chờ ảnh hiện tại xử lý xong...")
        if self._on_cancel is not None:
            self._on_cancel()

    def _apply_local_style(self):
        if self._dark:
            bg = "#1E2233"
            border = "#333A56"
            subtitle_color = "#9AA3C7"
            bar_bg = "#2A2F47"
        else:
            bg = "#FFFFFF"
            border = "#DCE3EE"
            subtitle_color = "#6B7690"
            bar_bg = "#EEF3FA"

        self.setStyleSheet(f"""
            QDialog {{
                background-color: {bg};
                border: 1px solid {border};
            }}
            QLabel#subtitle {{
                color: {subtitle_color};
                font-size: 11px;
            }}
            QProgressBar {{
                background-color: {bar_bg};
                border: 1px solid {border};
                border-radius: 6px;
                text-align: center;
                height: 18px;
            }}
            QProgressBar::chunk {{
                background-color: #3B7DDB;
                border-radius: 6px;
            }}
            QPushButton#secondaryBtn {{
                background: transparent;
                border: 1px solid {border};
                color: {subtitle_color};
                border-radius: 6px;
                padding: 4px 10px;
            }}
            QPushButton#secondaryBtn:hover {{
                background-color: {bar_bg};
            }}
            QPushButton#secondaryBtn:disabled {{
                color: #999;
            }}
        """)
