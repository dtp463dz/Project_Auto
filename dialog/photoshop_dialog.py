import os
import cv2
import numpy as np

from PyQt5.QtWidgets import (
    QDialog, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QFileDialog, QMessageBox, QRadioButton, QButtonGroup, QSlider,
    QInputDialog, QFrame
)
from PyQt5.QtCore import Qt, QRect, QRectF, QPoint, QPointF, pyqtSignal
from PyQt5.QtGui import QPixmap, QImage, QPainter, QPen, QColor, QCursor

from logic.composite_logic import cut_patch, composite_paste

def cv2_to_qpixmap(bgr):
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    h, w = rgb.shape[:2]
    qimg = QImage(rgb.data, w, h, w * 3, QImage.Format_RGB888)
    return QPixmap.fromImage(qimg.copy())


class _BaseImageCanvas(QWidget):
    """Canvas dùng chung: hiển thị 1 ảnh có ZOOM + PAN (giống Photoshop/Paint).

    - Ctrl + cuộn chuột: zoom quanh vị trí con trỏ (không lệch tâm qua nhiều lần zoom)
    - Kéo chuột giữa (middle button): pan
    - zoom_to_fit(): đưa về vừa khung nhìn
    100% = 1 pixel ảnh = 1 pixel màn hình (đúng chuẩn Paint), không phải 100% = fit.
    """

    zoom_changed = pyqtSignal(int)   # % zoom hiện tại

    MIN_SCALE = 0.05
    MAX_SCALE = 20.0

    def __init__(self, parent=None):
        super().__init__(parent)
        self.image_bgr = None
        self.pixmap = None
        self.scale = 1.0
        self.offset = QPointF(0, 0)
        self._panning = False
        self._pan_start = None
        self.setMinimumSize(360, 360)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)

    # ---------- load ----------
    def load_image(self, path):
        img = cv2.imread(path)
        if img is None:
            return False
        self.image_bgr = img
        self.pixmap = cv2_to_qpixmap(img)
        self.zoom_to_fit()
        return True

    def set_image_bgr(self, img_bgr):
        self.image_bgr = img_bgr
        self.pixmap = cv2_to_qpixmap(img_bgr)
        self.zoom_to_fit()

    # ---------- toạ độ ----------
    def to_canvas(self, pt_img) -> QPointF:
        return QPointF(
            pt_img.x() * self.scale + self.offset.x(),
            pt_img.y() * self.scale + self.offset.y()
        )

    def to_image(self, pt_canvas) -> QPointF:
        return QPointF(
            (pt_canvas.x() - self.offset.x()) / self.scale,
            (pt_canvas.y() - self.offset.y()) / self.scale
        )

    def rect_to_canvas(self, rect_img: QRectF) -> QRectF:
        tl = self.to_canvas(rect_img.topLeft())
        return QRectF(tl.x(), tl.y(),
                       rect_img.width() * self.scale,
                       rect_img.height() * self.scale)

    # ---------- zoom ----------
    def _fit_scale_value(self):
        if not self.pixmap:
            return 1.0
        pw, ph = self.pixmap.width(), self.pixmap.height()
        cw, ch = max(1, self.width()), max(1, self.height())
        return min(cw / pw, ch / ph)

    def zoom_to_fit(self):
        if not self.pixmap:
            return
        self.scale = self._fit_scale_value()
        pw, ph = self.pixmap.width(), self.pixmap.height()
        cw, ch = max(1, self.width()), max(1, self.height())
        draw_w, draw_h = pw * self.scale, ph * self.scale
        self.offset = QPointF((cw - draw_w) / 2, (ch - draw_h) / 2)
        self.update()
        self._emit_zoom()

    def _emit_zoom(self):
        self.zoom_changed.emit(int(round(self.scale * 100)))

    def zoom_in(self):
        self._zoom_around_center(1.25)

    def zoom_out(self):
        self._zoom_around_center(1 / 1.25)

    def _zoom_around_center(self, factor):
        if not self.pixmap:
            return
        center = QPointF(self.width() / 2, self.height() / 2)
        anchor_img = self.to_image(center)
        new_scale = max(self.MIN_SCALE, min(self.scale * factor, self.MAX_SCALE))
        if abs(new_scale - self.scale) < 1e-9:
            return
        self.scale = new_scale
        self.offset = QPointF(
            center.x() - anchor_img.x() * self.scale,
            center.y() - anchor_img.y() * self.scale
        )
        self.update()
        self._emit_zoom()

    def wheelEvent(self, event):
        if not self.pixmap or not (event.modifiers() & Qt.ControlModifier):
            event.ignore()
            return
        mouse_pos = QPointF(event.pos())
        old_pos = self.to_image(mouse_pos)
        factor = 1.25 if event.angleDelta().y() > 0 else 1 / 1.25
        new_scale = max(self.MIN_SCALE, min(self.scale * factor, self.MAX_SCALE))
        if abs(new_scale - self.scale) > 1e-9:
            self.scale = new_scale
            self.offset = QPointF(
                mouse_pos.x() - old_pos.x() * self.scale,
                mouse_pos.y() - old_pos.y() * self.scale
            )
            self.update()
            self._emit_zoom()
        event.accept()

    # ---------- pan (middle-mouse-drag) - subclass gọi các hàm này TRƯỚC ----------
    def _try_start_pan(self, event):
        if event.button() == Qt.MiddleButton:
            self._panning = True
            self._pan_start = event.pos()
            self.setCursor(Qt.ClosedHandCursor)
            return True
        return False

    def _try_pan_move(self, event):
        if self._panning:
            delta = event.pos() - self._pan_start
            self.offset += QPointF(delta)
            self._pan_start = event.pos()
            self.update()
            return True
        return False

    def _try_end_pan(self, event):
        if self._panning and event.button() == Qt.MiddleButton:
            self._panning = False
            self.setCursor(Qt.ArrowCursor)
            return True
        return False

    def _draw_background(self, painter):
        painter.fillRect(self.rect(), QColor(30, 30, 30))
        if self.pixmap:
            painter.drawPixmap(
                self.rect_to_canvas(QRectF(0, 0, self.pixmap.width(), self.pixmap.height())),
                self.pixmap, QRectF(self.pixmap.rect())
            )


class SourceCanvas(_BaseImageCanvas):
    """Ảnh nguồn - chọn vùng cắt theo bbox có sẵn (mode='bbox') hoặc tự vẽ
    hình chữ nhật kiểu Paint: vẽ thô rồi kéo góc để resize, kéo giữa để
    di chuyển (mode='manual')."""

    selection_changed = pyqtSignal()
    HANDLE_SIZE = 9

    def __init__(self, parent=None):
        super().__init__(parent)
        self.mode = "bbox"
        self.boxes = []
        self.selected_idx = None
        self.manual_rect = None
        self._drag_start = None
        self.resize_handle = None
        self.moving = False
        self._move_offset = QPointF()

    def set_mode(self, mode):
        self.mode = mode
        self.selected_idx = None
        self.manual_rect = None
        self.update()
        self.selection_changed.emit()

    def load_boxes_from_txt(self, txt_path, project_labels):
        self.boxes = []
        if not os.path.exists(txt_path) or self.image_bgr is None:
            self.update()
            return
        h, w = self.image_bgr.shape[:2]
        with open(txt_path, "r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) != 5:
                    continue
                cls_id = int(parts[0])
                x, y, bw, bh = map(float, parts[1:])
                cx, cy = x * w, y * h
                rw, rh = bw * w, bh * h
                rect = QRectF(cx - rw / 2, cy - rh / 2, rw, rh)
                name = project_labels[cls_id] if 0 <= cls_id < len(project_labels) else str(cls_id)
                self.boxes.append({"rect": rect, "label_name": name})
        self.selected_idx = None
        self.update()

    def get_cut(self):
        if self.mode == "bbox":
            if self.selected_idx is None:
                return None, None
            b = self.boxes[self.selected_idx]
            r = b["rect"]
            return QRect(int(r.x()), int(r.y()), int(r.width()), int(r.height())), b["label_name"]
        else:
            if self.manual_rect is None or self.manual_rect.normalized().width() < 4 \
                    or self.manual_rect.normalized().height() < 4:
                return None, None
            r = self.manual_rect.normalized()
            return QRect(int(r.x()), int(r.y()), int(r.width()), int(r.height())), None

    def _detect_handle(self, pos_canvas, rect_canvas):
        pts = {
            'tl': rect_canvas.topLeft(), 'tr': rect_canvas.topRight(),
            'bl': rect_canvas.bottomLeft(), 'br': rect_canvas.bottomRight(),
        }
        tol = self.HANDLE_SIZE * 1.4
        for name, pt in pts.items():
            if (pos_canvas - pt).manhattanLength() <= tol:
                return name
        return None

    # ---- mouse ----
    def mousePressEvent(self, event):
        if self._try_start_pan(event):
            return
        if self.pixmap is None or event.button() != Qt.LeftButton:
            return
        if self.mode == "bbox":
            pos_img = self.to_image(event.pos())
            for idx in reversed(range(len(self.boxes))):
                if self.boxes[idx]["rect"].contains(pos_img):
                    self.selected_idx = idx
                    self.update()
                    self.selection_changed.emit()
                    return
            return

        # ---- manual: ưu tiên handle -> di chuyển -> vẽ mới ----
        pos_canvas = QPointF(event.pos())
        if self.manual_rect is not None:
            rect_canvas = self.rect_to_canvas(self.manual_rect.normalized())
            handle = self._detect_handle(pos_canvas, rect_canvas)
            if handle:
                self.resize_handle = handle
                return
            if rect_canvas.contains(pos_canvas):
                self.moving = True
                self._move_offset = self.to_image(pos_canvas) - self.manual_rect.normalized().topLeft()
                return

        self._drag_start = self.to_image(pos_canvas)
        self.manual_rect = QRectF(self._drag_start, self._drag_start)
        self.update()

    def mouseMoveEvent(self, event):
        if self._try_pan_move(event):
            return
        if self.mode != "manual":
            return

        pos_canvas = QPointF(event.pos())

        # hover cursor cho handle (chỉ khi không đang thao tác gì)
        if not self.resize_handle and not self.moving and self._drag_start is None and self.manual_rect is not None:
            rect_canvas = self.rect_to_canvas(self.manual_rect.normalized())
            handle = self._detect_handle(pos_canvas, rect_canvas)
            cursor_map = {'tl': Qt.SizeFDiagCursor, 'br': Qt.SizeFDiagCursor,
                          'tr': Qt.SizeBDiagCursor, 'bl': Qt.SizeBDiagCursor}
            if handle:
                self.setCursor(cursor_map[handle])
            elif rect_canvas.contains(pos_canvas):
                self.setCursor(Qt.SizeAllCursor)
            else:
                self.setCursor(Qt.CrossCursor)

        pos_img = self.to_image(event.pos())
        if self.resize_handle:
            r = self.manual_rect.normalized()
            left, top, right, bottom = r.left(), r.top(), r.right(), r.bottom()
            if 'l' in self.resize_handle:
                left = pos_img.x()
            if 'r' in self.resize_handle:
                right = pos_img.x()
            if 't' in self.resize_handle:
                top = pos_img.y()
            if 'b' in self.resize_handle:
                bottom = pos_img.y()
            self.manual_rect = QRectF(QPointF(left, top), QPointF(right, bottom))
            self.update()
        elif self.moving:
            new_tl = pos_img - self._move_offset
            r = self.manual_rect.normalized()
            self.manual_rect = QRectF(new_tl, QPointF(new_tl.x() + r.width(), new_tl.y() + r.height()))
            self.update()
        elif self._drag_start is not None:
            self.manual_rect = QRectF(self._drag_start, pos_img)
            self.update()

    def mouseReleaseEvent(self, event):
        if self._try_end_pan(event):
            return
        if self.mode == "manual":
            if self.resize_handle or self.moving or self._drag_start is not None:
                self.resize_handle = None
                self.moving = False
                self._drag_start = None
                self.selection_changed.emit()

    def paintEvent(self, event):
        painter = QPainter(self)
        self._draw_background(painter)
        if self.mode == "bbox":
            for idx, b in enumerate(self.boxes):
                rc = self.rect_to_canvas(b["rect"])
                pen = QPen(QColor(80, 200, 255) if idx != self.selected_idx else QColor(255, 200, 40), 2)
                painter.setPen(pen)
                painter.setBrush(Qt.NoBrush)
                painter.drawRect(rc)
                if idx == self.selected_idx:
                    painter.fillRect(rc, QColor(255, 200, 40, 60))
        else:
            if self.manual_rect is not None:
                rc = self.rect_to_canvas(self.manual_rect.normalized())
                painter.setPen(QPen(QColor(255, 200, 40), 2, Qt.DashLine))
                painter.setBrush(QColor(255, 200, 40, 60))
                painter.drawRect(rc)
                # handle kiểu Paint - 4 ô vuông nhỏ ở góc
                s = self.HANDLE_SIZE
                painter.setPen(QPen(QColor(60, 60, 60), 1))
                painter.setBrush(QColor(255, 255, 255))
                for pt in (rc.topLeft(), rc.topRight(), rc.bottomLeft(), rc.bottomRight()):
                    painter.drawRect(QRectF(pt.x() - s / 2, pt.y() - s / 2, s, s))


class TargetCanvas(_BaseImageCanvas):
    """Ảnh đích - kéo-thả patch đã cắt vào vị trí mong muốn, chỉnh tỉ lệ."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.patch_bgr = None
        self.patch_scale = 1.0
        self.patch_pos_img = QPointF(0, 0)
        self._dragging = False
        self._drag_offset = QPointF(0, 0)

    def set_patch(self, patch_bgr):
        self.patch_bgr = patch_bgr
        self.patch_scale = 1.0
        if self.image_bgr is not None:
            th, tw = self.image_bgr.shape[:2]
            ph, pw = patch_bgr.shape[:2]
            self.patch_pos_img = QPointF((tw - pw) / 2, (th - ph) / 2)
        self.update()

    def clear_patch(self):
        self.patch_bgr = None
        self.update()

    def _patch_size(self):
        if self.patch_bgr is None:
            return 0, 0
        h, w = self.patch_bgr.shape[:2]
        return int(w * self.patch_scale), int(h * self.patch_scale)

    def get_paste_rect(self):
        w, h = self._patch_size()
        return int(self.patch_pos_img.x()), int(self.patch_pos_img.y()), w, h

    def set_scale_percent(self, percent):
        self.patch_scale = percent / 100.0
        self.update()

    def mousePressEvent(self, event):
        if self._try_start_pan(event):
            return
        if self.patch_bgr is None or event.button() != Qt.LeftButton:
            return
        pos_img = self.to_image(event.pos())
        w, h = self._patch_size()
        patch_rect = QRectF(self.patch_pos_img.x(), self.patch_pos_img.y(), w, h)
        if patch_rect.contains(pos_img):
            self._dragging = True
            self._drag_offset = pos_img - self.patch_pos_img
            self.setCursor(Qt.ClosedHandCursor)

    def mouseMoveEvent(self, event):
        if self._try_pan_move(event):
            return
        if self._dragging:
            pos_img = self.to_image(event.pos())
            self.patch_pos_img = pos_img - self._drag_offset
            self.update()

    def mouseReleaseEvent(self, event):
        if self._try_end_pan(event):
            return
        if self._dragging:
            self._dragging = False
            self.setCursor(Qt.ArrowCursor)

    def paintEvent(self, event):
        painter = QPainter(self)
        self._draw_background(painter)
        if self.patch_bgr is not None:
            w, h = self._patch_size()
            if w > 0 and h > 0:
                patch_resized = cv2.resize(self.patch_bgr, (w, h))
                patch_pix = cv2_to_qpixmap(patch_resized)
                rc = self.rect_to_canvas(QRectF(self.patch_pos_img.x(), self.patch_pos_img.y(), w, h))
                painter.setOpacity(0.85)
                painter.drawPixmap(rc, patch_pix, QRectF(patch_pix.rect()))
                painter.setOpacity(1.0)
                painter.setPen(QPen(QColor(80, 220, 120), 2, Qt.DashLine))
                painter.setBrush(Qt.NoBrush)
                painter.drawRect(rc)


def _make_zoom_row(canvas):
    """Tạo hàng điều khiển zoom kiểu Paint: － [ 100% ] ＋ [Fit]"""
    row = QHBoxLayout()
    btn_out = QPushButton("－")
    btn_out.setObjectName("navBtn")
    btn_out.setFixedWidth(32)
    zoom_label = QLabel("100%")
    zoom_label.setFixedWidth(48)
    zoom_label.setAlignment(Qt.AlignCenter)
    btn_in = QPushButton("＋")
    btn_in.setObjectName("navBtn")
    btn_in.setFixedWidth(32)
    btn_fit = QPushButton("Fit")
    btn_fit.setObjectName("navBtn")
    btn_fit.setFixedWidth(40)

    btn_out.clicked.connect(canvas.zoom_out)
    btn_in.clicked.connect(canvas.zoom_in)
    btn_fit.clicked.connect(canvas.zoom_to_fit)
    canvas.zoom_changed.connect(lambda p: zoom_label.setText(f"{p}%"))

    row.addWidget(QLabel("🔍"))
    row.addWidget(btn_out)
    row.addWidget(zoom_label)
    row.addWidget(btn_in)
    row.addWidget(btn_fit)
    row.addStretch()
    hint = QLabel("Ctrl+cuộn: zoom · Chuột giữa: pan")
    hint.setObjectName("subtitle")
    row.addWidget(hint)
    return row


class PhotoshopDialog(QDialog):
    """Cửa sổ ghép ảnh: cắt vật thể từ ảnh nguồn (theo bbox có sẵn hoặc tự vẽ
    kiểu Paint - kéo góc resize, kéo giữa di chuyển), dán vào ảnh đích với
    biên mờ nhẹ (feathering), lưu thành ảnh mới + tự sinh label cho vật vừa dán.
    Cả 2 khung ảnh đều zoom/pan được (Ctrl+cuộn chuột, chuột giữa để pan)."""

    def __init__(self, main_window):
        super().__init__(main_window)
        self.main_window = main_window
        self.setWindowTitle("🧩 Photoshop - Ghép ảnh tạo data")
        self.resize(1200, 720)

        self.source_path = None
        self.target_path = None
        self.cut_label_name = None
        self._dark = getattr(main_window, "current_theme", "light") == "dark"

        root = QVBoxLayout(self)

        # ---------- hàng trên: 2 canvas ----------
        canvas_row = QHBoxLayout()

        src_col = QVBoxLayout()
        src_header = QHBoxLayout()
        src_header.addWidget(QLabel("① Ảnh nguồn (cắt vật thể)"))
        self.btn_src_open = QPushButton("📂 Mở ảnh...")
        self.btn_src_current = QPushButton("Dùng ảnh đang mở")
        src_header.addStretch()
        src_header.addWidget(self.btn_src_current)
        src_header.addWidget(self.btn_src_open)
        src_col.addLayout(src_header)

        mode_row = QHBoxLayout()
        self.radio_bbox = QRadioButton("🔲 Chọn theo bbox có sẵn")
        self.radio_manual = QRadioButton("✏️ Tự vẽ vùng cắt (như Paint)")
        self.radio_bbox.setChecked(True)
        mode_group = QButtonGroup(self)
        mode_group.addButton(self.radio_bbox)
        mode_group.addButton(self.radio_manual)
        mode_row.addWidget(self.radio_bbox)
        mode_row.addWidget(self.radio_manual)
        mode_row.addStretch()
        src_col.addLayout(mode_row)

        self.source_canvas = SourceCanvas()
        src_col.addWidget(self.source_canvas, 1)
        src_col.addLayout(_make_zoom_row(self.source_canvas))

        self.btn_cut = QPushButton("✂️  Cắt vùng đã chọn →")
        self.btn_cut.setObjectName("successBtn")
        src_col.addWidget(self.btn_cut)

        tgt_col = QVBoxLayout()
        tgt_header = QHBoxLayout()
        tgt_header.addWidget(QLabel("② Ảnh đích (kéo-thả để đặt vị trí)"))
        self.btn_tgt_open = QPushButton("📂 Mở ảnh...")
        self.btn_tgt_current = QPushButton("Dùng ảnh đang mở")
        tgt_header.addStretch()
        tgt_header.addWidget(self.btn_tgt_current)
        tgt_header.addWidget(self.btn_tgt_open)
        tgt_col.addLayout(tgt_header)

        scale_row = QHBoxLayout()
        scale_row.addWidget(QLabel("Tỉ lệ patch:"))
        self.scale_slider = QSlider(Qt.Horizontal)
        self.scale_slider.setRange(20, 200)
        self.scale_slider.setValue(100)
        self.scale_value_label = QLabel("100%")
        self.scale_value_label.setFixedWidth(40)
        scale_row.addWidget(self.scale_slider)
        scale_row.addWidget(self.scale_value_label)
        tgt_col.addLayout(scale_row)

        self.target_canvas = TargetCanvas()
        tgt_col.addWidget(self.target_canvas, 1)
        tgt_col.addLayout(_make_zoom_row(self.target_canvas))

        feather_row = QHBoxLayout()
        feather_row.addWidget(QLabel("Độ mờ viền (feather):"))
        self.feather_slider = QSlider(Qt.Horizontal)
        self.feather_slider.setRange(0, 40)
        self.feather_slider.setValue(12)
        self.feather_value_label = QLabel("12px")
        self.feather_value_label.setFixedWidth(40)
        feather_row.addWidget(self.feather_slider)
        feather_row.addWidget(self.feather_value_label)
        tgt_col.addLayout(feather_row)

        canvas_row.addLayout(src_col, 1)
        canvas_row.addLayout(tgt_col, 1)
        root.addLayout(canvas_row, 1)

        # ---------- trạng thái + nút lưu ----------
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        root.addWidget(line)

        bottom_row = QHBoxLayout()
        self.status_label = QLabel("Chưa cắt vùng nào.")
        self.status_label.setObjectName("subtitle")
        bottom_row.addWidget(self.status_label, 1)

        self.btn_save = QPushButton("💾  Lưu ảnh ghép")
        self.btn_save.setObjectName("successBtn")
        self.btn_save.setEnabled(False)
        bottom_row.addWidget(self.btn_save)
        root.addLayout(bottom_row)

        self._apply_local_style()

        # ---------- kết nối ----------
        self.btn_src_open.clicked.connect(self._open_source_file)
        self.btn_src_current.clicked.connect(self._use_current_as_source)
        self.btn_tgt_open.clicked.connect(self._open_target_file)
        self.btn_tgt_current.clicked.connect(self._use_current_as_target)
        self.radio_bbox.toggled.connect(self._on_mode_toggled)
        self.source_canvas.selection_changed.connect(self._update_status)
        self.btn_cut.clicked.connect(self._do_cut)
        self.scale_slider.valueChanged.connect(self._on_scale_changed)
        self.feather_slider.valueChanged.connect(self._on_feather_changed)
        self.btn_save.clicked.connect(self._do_save)

    # ---------- style ----------
    def _apply_local_style(self):
        subtitle = "#9AA3C7" if self._dark else "#6B7690"
        self.setStyleSheet(f"QLabel#subtitle {{ color: {subtitle}; font-size: 11px; }}")

    # ---------- nguồn ----------
    def _open_source_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Chọn ảnh nguồn", "", "Images (*.jpg *.jpeg *.png *.bmp)")
        if not path:
            return
        self._load_source(path)

    def _use_current_as_source(self):
        mw = self.main_window
        if not mw.current_images or not (0 <= mw.current_index < len(mw.current_images)):
            QMessageBox.warning(self, "Chưa có ảnh", "Chưa mở ảnh nào trong TPLabel.")
            return
        self._load_source(mw.current_images[mw.current_index])

    def _load_source(self, path):
        if not self.source_canvas.load_image(path):
            QMessageBox.warning(self, "Lỗi", f"Không đọc được ảnh:\n{path}")
            return
        self.source_path = path
        mw = self.main_window
        txt_path = None
        if mw.labels_dir:
            name = os.path.splitext(os.path.basename(path))[0]
            txt_path = os.path.join(mw.labels_dir, name + ".txt")
        if txt_path:
            self.source_canvas.load_boxes_from_txt(txt_path, mw.labels)
        self._update_status()

    def _on_mode_toggled(self, checked):
        self.source_canvas.set_mode("bbox" if self.radio_bbox.isChecked() else "manual")

    # ---------- đích ----------
    def _open_target_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Chọn ảnh đích", "", "Images (*.jpg *.jpeg *.png *.bmp)")
        if not path:
            return
        self._load_target(path)

    def _use_current_as_target(self):
        mw = self.main_window
        if not mw.current_images or not (0 <= mw.current_index < len(mw.current_images)):
            QMessageBox.warning(self, "Chưa có ảnh", "Chưa mở ảnh nào trong TPLabel.")
            return
        self._load_target(mw.current_images[mw.current_index])

    def _load_target(self, path):
        if not self.target_canvas.load_image(path):
            QMessageBox.warning(self, "Lỗi", f"Không đọc được ảnh:\n{path}")
            return
        self.target_path = path
        self._update_status()

    # ---------- cắt / kéo-thả ----------
    def _do_cut(self):
        rect, label_name = self.source_canvas.get_cut()
        if rect is None or rect.width() < 4 or rect.height() < 4:
            QMessageBox.information(self, "Chưa chọn vùng",
                                     "Hãy chọn 1 bbox có sẵn hoặc tự vẽ vùng cắt trước.")
            return
        if self.source_canvas.image_bgr is None:
            return

        patch, _ = cut_patch(self.source_canvas.image_bgr,
                              (rect.x(), rect.y(), rect.width(), rect.height()))

        if label_name is None:
            existing = list(self.main_window.labels)
            name, ok = QInputDialog.getItem(
                self, "Tên class", "Vật thể vừa cắt thuộc class nào?",
                existing if existing else [""], 0, True
            )
            if not ok or not name.strip():
                return
            label_name = name.strip()

        self.cut_label_name = label_name
        if self.target_canvas.pixmap is None:
            QMessageBox.information(self, "Chưa có ảnh đích", "Hãy mở ảnh đích trước khi dán.")
            return
        self.target_canvas.set_patch(patch)
        self._update_status()

    def _on_scale_changed(self, value):
        self.scale_value_label.setText(f"{value}%")
        self.target_canvas.set_scale_percent(value)

    def _on_feather_changed(self, value):
        self.feather_value_label.setText(f"{value}px")

    def _update_status(self):
        parts = []
        if self.source_path:
            parts.append(f"Nguồn: {os.path.basename(self.source_path)}")
        if self.target_path:
            parts.append(f"Đích: {os.path.basename(self.target_path)}")
        if self.cut_label_name and self.target_canvas.patch_bgr is not None:
            parts.append(f"Đã cắt: [{self.cut_label_name}] - kéo-thả trên ảnh đích rồi bấm Lưu")
        self.status_label.setText("   |   ".join(parts) if parts else "Chưa cắt vùng nào.")
        self.btn_save.setEnabled(
            self.target_canvas.patch_bgr is not None and self.target_path is not None
        )

    # ---------- lưu ----------
    def _do_save(self):
        mw = self.main_window
        if self.target_canvas.patch_bgr is None or self.target_canvas.image_bgr is None:
            return
        if not mw.labels_dir:
            QMessageBox.warning(self, "Chưa có Labels Folder",
                                 "Hãy chọn Labels Folder trong TPLabel trước khi lưu.")
            return

        x, y, w, h = self.target_canvas.get_paste_rect()
        feather_px = self.feather_slider.value()
        result_bgr, (px, py, pw, ph) = composite_paste(
            self.target_canvas.image_bgr, self.target_canvas.patch_bgr, x, y, feather_px
        )
        if pw <= 0 or ph <= 0:
            QMessageBox.warning(self, "Vị trí không hợp lệ",
                                 "Vùng dán nằm ngoài ảnh đích, hãy kéo lại vào trong ảnh.")
            return

        target_dir = os.path.dirname(self.target_path)
        base_name = os.path.splitext(os.path.basename(self.target_path))[0]
        ext = os.path.splitext(self.target_path)[1] or ".jpg"
        n = 1
        while True:
            new_name = f"{base_name}_ps{n}{ext}"
            new_path = os.path.join(target_dir, new_name)
            if not os.path.exists(new_path):
                break
            n += 1

        if not cv2.imwrite(new_path, result_bgr):
            QMessageBox.critical(self, "Lỗi", f"Không lưu được ảnh:\n{new_path}")
            return

        if self.cut_label_name not in mw.labels:
            mw.labels.append(self.cut_label_name)
            mw.refresh_label_list()
            mw.save_classes_file()
        label_id = mw.labels.index(self.cut_label_name)

        th, tw = self.target_canvas.image_bgr.shape[:2]
        cx = (px + pw / 2) / tw
        cy = (py + ph / 2) / th
        nw = pw / tw
        nh = ph / th

        label_path = os.path.join(mw.labels_dir, new_name.rsplit(".", 1)[0] + ".txt")
        with open(label_path, "w", encoding="utf-8") as f:
            f.write(f"{label_id} {cx:.6f} {cy:.6f} {nw:.6f} {nh:.6f}\n")

        if mw.current_images and target_dir == os.path.dirname(mw.current_images[0]):
            mw.current_images.append(new_path)
            mw.refresh_image_list()

        QMessageBox.information(
            self, "Đã lưu",
            f"✅ Đã lưu ảnh ghép: {new_name}\n"
            f"Label: [{self.cut_label_name}] tại ({px},{py},{pw}x{ph})"
        )

        self.target_canvas.clear_patch()
        self.cut_label_name = None
        self._update_status()