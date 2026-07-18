import os

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QSlider, QDoubleSpinBox, QPushButton, QFrame, QSizePolicy
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont


class AutoLabelConfirmDialog(QDialog):
    """Dialog xác nhận trước khi chạy auto-label, cho phép chỉnh confidence
    threshold ngay trên UI thay vì hardcode trong code."""

    DEFAULT_CONF = 0.4

    def __init__(self, parent, image_count, model_path, label_dir):
        super().__init__(parent)
        self._conf = self.DEFAULT_CONF
        self._dark = getattr(parent, "current_theme", "light") == "dark"

        self.setWindowTitle("Auto Label")
        self.setMinimumWidth(440)
        self._apply_local_style()

        root = QVBoxLayout(self)
        root.setContentsMargins(22, 20, 22, 18)
        root.setSpacing(14)

        # ---------- Header ----------
        header = QHBoxLayout()
        icon = QLabel("🤖")
        icon.setStyleSheet("font-size: 26px;")
        title_box = QVBoxLayout()
        title_box.setSpacing(0)
        title = QLabel("Auto Label")
        title.setFont(self._font(15, bold=True))
        subtitle = QLabel("Tự động gán nhãn bằng model YOLO")
        subtitle.setObjectName("subtitle")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        header.addWidget(icon)
        header.addSpacing(8)
        header.addLayout(title_box)
        header.addStretch()
        root.addLayout(header)

        # ---------- Info card ----------
        info_card = QFrame()
        info_card.setObjectName("card")
        info_layout = QVBoxLayout(info_card)
        info_layout.setSpacing(8)
        info_layout.setContentsMargins(14, 12, 14, 12)

        info_layout.addWidget(self._info_row("📂", "Số ảnh", f"{image_count} ảnh"))
        info_layout.addWidget(self._info_row("🧠", "Model", os.path.basename(model_path)))
        info_layout.addWidget(self._info_row("📁", "Thư mục output", label_dir, elide=True))
        root.addWidget(info_card)

        # ---------- Confidence card ----------
        conf_card = QFrame()
        conf_card.setObjectName("card")
        conf_layout = QVBoxLayout(conf_card)
        conf_layout.setSpacing(6)
        conf_layout.setContentsMargins(14, 12, 14, 14)

        conf_title_row = QHBoxLayout()
        conf_title = QLabel("🎯  Confidence threshold")
        conf_title.setFont(self._font(12, bold=True))
        self.conf_badge = QLabel()
        self.conf_badge.setAlignment(Qt.AlignCenter)
        self.conf_badge.setFixedWidth(56)
        conf_title_row.addWidget(conf_title)
        conf_title_row.addStretch()
        conf_title_row.addWidget(self.conf_badge)
        conf_layout.addLayout(conf_title_row)

        conf_hint = QLabel(
            "Chỉ giữ lại phát hiện có độ tin cậy ≥ giá trị này. "
            "Thấp hơn → nhiều box hơn nhưng dễ sai. "
            "Cao hơn → ít box hơn nhưng chắc chắn hơn."
        )
        conf_hint.setWordWrap(True)
        conf_hint.setObjectName("subtitle")
        conf_layout.addWidget(conf_hint)

        conf_row = QHBoxLayout()
        conf_row.setSpacing(10)

        self.low_label = QLabel("0.05")
        self.low_label.setObjectName("subtitle")
        self.high_label = QLabel("0.95")
        self.high_label.setObjectName("subtitle")

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(5, 95)
        self.slider.setValue(int(self.DEFAULT_CONF * 100))
        self.slider.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.spin = QDoubleSpinBox()
        self.spin.setRange(0.05, 0.95)
        self.spin.setSingleStep(0.05)
        self.spin.setDecimals(2)
        self.spin.setValue(self.DEFAULT_CONF)
        self.spin.setFixedWidth(72)

        self.slider.valueChanged.connect(self._on_slider_changed)
        self.spin.valueChanged.connect(self._on_spin_changed)

        conf_row.addWidget(self.low_label)
        conf_row.addWidget(self.slider)
        conf_row.addWidget(self.high_label)
        conf_row.addWidget(self.spin)
        conf_layout.addLayout(conf_row)

        root.addWidget(conf_card)
        self._update_badge(self.DEFAULT_CONF)

        # ---------- Buttons ----------
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_cancel = QPushButton("Hủy")
        btn_cancel.setObjectName("secondaryBtn")
        btn_cancel.setFixedHeight(34)
        btn_ok = QPushButton("▶  Chạy Auto Label")
        btn_ok.setFixedHeight(34)
        btn_ok.setDefault(True)
        btn_cancel.clicked.connect(self.reject)
        btn_ok.clicked.connect(self.accept)
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_ok)
        root.addLayout(btn_row)

    # ---------- helpers ----------
    def _font(self, size, bold=False):
        f = QFont()
        f.setPointSize(size)
        f.setBold(bold)
        return f

    def _info_row(self, emoji, label, value, elide=False):
        row = QFrame()
        h = QHBoxLayout(row)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(8)
        icon = QLabel(emoji)
        icon.setFixedWidth(20)
        name = QLabel(label)
        name.setObjectName("subtitle")
        name.setFixedWidth(100)
        val = QLabel(value)
        val.setFont(self._font(10, bold=True))
        if elide:
            val.setToolTip(value)
        h.addWidget(icon)
        h.addWidget(name)
        h.addWidget(val, 1)
        return row

    def _on_slider_changed(self, value):
        conf = value / 100.0
        if abs(self.spin.value() - conf) > 1e-6:
            self.spin.blockSignals(True)
            self.spin.setValue(conf)
            self.spin.blockSignals(False)
        self._conf = conf
        self._update_badge(conf)

    def _on_spin_changed(self, value):
        slider_val = int(round(value * 100))
        if self.slider.value() != slider_val:
            self.slider.blockSignals(True)
            self.slider.setValue(slider_val)
            self.slider.blockSignals(False)
        self._conf = value
        self._update_badge(value)

    def _update_badge(self, conf):
        if conf < 0.3:
            color = "#E0554F"    # đỏ nhạt - dễ bắt nhầm
        elif conf < 0.6:
            color = "#2E9E5B"    # xanh lá - vùng khuyến nghị
        else:
            color = "#3B7DDB"    # xanh dương - chặt chẽ, ít box
        self.conf_badge.setText(f"{conf:.2f}")
        self.conf_badge.setStyleSheet(
            f"background-color:{color}; color:white; border-radius:8px; "
            f"padding:3px 8px; font-weight:bold;"
        )

    def _apply_local_style(self):
        if self._dark:
            card_bg = "#242840"
            card_border = "#37406A"
            subtitle_color = "#9AA3C7"
        else:
            card_bg = "#F5F7FC"
            card_border = "#DCE3EE"
            subtitle_color = "#6B7690"

        self.setStyleSheet(f"""
            QFrame#card {{
                background-color: {card_bg};
                border: 1px solid {card_border};
                border-radius: 10px;
            }}
            QLabel#subtitle {{
                color: {subtitle_color};
                font-size: 11px;
            }}
            QPushButton#secondaryBtn {{
                background: transparent;
                border: 1px solid {card_border};
                color: {subtitle_color};
            }}
            QPushButton#secondaryBtn:hover {{
                background-color: {card_bg};
            }}
        """)

    def get_conf(self):
        return round(self._conf, 2)