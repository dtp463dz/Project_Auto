from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QPen, QPixmap, QColor, QCursor
from PyQt5.QtCore import Qt, QRect, QPoint, pyqtSignal, QSize, QPointF, QRectF, QSizeF
import colorsys
from gui.logger import setup_logger
log = setup_logger()

class ImageCanvas(QWidget):
    box_created = pyqtSignal(QRectF)
    box_double_clicked = pyqtSignal(int)
    boxes_changed = pyqtSignal()
    box_selected = pyqtSignal(int)
    key_next_pressed = pyqtSignal()
    key_prev_pressed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.pixmap = None
        self.scale = 1.0
        self.boxes = []
        self.undo_stack = []
        self.redo_stack = []
        self.drawing = False
        self.current_label = None
        self.current_rect = None
        self.start_pos = None
        self.selected_box = None
        self.resize_mode = None # tl, tr,bl, br
        self.dragging = False
        self.drag_offset = QPoint()
        self.offset = QPoint(0, 0)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)
        self.panning = False
        self.last_pan_pos = None
        self.hidden_labels = set()
        self._real_change = False   # True chỉ khi mousePressEvent->mouseMoveEvent thực sự làm thay đổi rect (không phải chỉ click chọn)

    def load_image(self, path):
        self.pixmap = QPixmap(path)
        if self.pixmap.isNull():
            return
        self.scale = self.fit_scale()
        self.center_image()
        self.boxes.clear()
        self.undo_stack.clear()
        self.redo_stack.clear()
        self.current_rect = None
        self.start_pos = None
        self.update()

    def paintEvent(self, event):
        if not self.pixmap:
            return

        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)
        painter.save()
        painter.translate(self.offset)
        painter.scale(self.scale, self.scale)
        painter.drawPixmap(0, 0, self.pixmap)

        # vẽ box 
        for idx, item in enumerate(self.boxes):
            if item["label"] in self.hidden_labels:
                continue
            rect = item["rect"]
            color = self.get_label_color(item["label"])
            if self.selected_box == idx:
                pen = QPen(Qt.white, 2 / self.scale)
                fill = QColor(color)
                fill.setAlpha(60)
            else:
                pen = QPen(color, 2 / self.scale)
                fill = QColor(color)
                fill.setAlpha(28)          

            pen.setCosmetic(False)
            painter.setPen(pen)
            painter.setBrush(fill)
            painter.drawRect(rect)
            if self.selected_box == idx:
                self.draw_handles(painter, rect, color)

        # drawing bbox(realtime)
        if self.current_rect:
            rect = self.current_rect.normalized()
            color = self.get_label_color(self.current_label) if self.current_label is not None else QColor(Qt.red)
            pen = QPen(color, 1.5 / self.scale)
            painter.setPen(pen)
            painter.drawRect(rect)
            self.draw_handles(painter, rect, color)
        painter.restore()
        font = painter.font()
        font.setPixelSize(12)
        font.setBold(True)
        painter.setFont(font)
        metrics = painter.fontMetrics()

        for idx, item in enumerate(self.boxes):
            if item["label"] in self.hidden_labels:
                continue
            label_name = str(item.get("label_name", ""))
            if not label_name:
                continue
            color = self.get_label_color(item["label"])
            chip_color = color.darker(115)          
            text_color = self.get_contrast_text_color(chip_color)
            rect_canvas = self.map_to_canvas(item["rect"])
            pad_x, pad_y = 5, 3
            text_w = metrics.horizontalAdvance(label_name) + pad_x * 2
            text_h = metrics.height() + pad_y * 2
            chip_x = rect_canvas.left()
            chip_y = rect_canvas.top() - text_h
            if chip_y < 0:                          
                chip_y = rect_canvas.top() + 2

            chip_rect = QRectF(chip_x, chip_y, text_w, text_h)
            painter.setPen(Qt.NoPen)
            painter.setBrush(chip_color)
            painter.drawRoundedRect(chip_rect, 3, 3)
            painter.setPen(text_color)
            painter.drawText(
                chip_rect.adjusted(pad_x, pad_y, -pad_x, -pad_y),
                Qt.AlignLeft | Qt.AlignVCenter,
                label_name
            )
    
    def map_to_image(self, pos):
        x = (pos.x() - self.offset.x()) / self.scale
        y = (pos.y() - self.offset.y()) / self.scale
        return QPoint(int(x), int(y))

    def map_to_image_f(self, pos):
        """Giống map_to_image nhưng giữ nguyên độ chính xác float -
        bắt buộc dùng cho zoom-to-cursor để tránh lệch tâm cộng dồn qua nhiều lần zoom."""
        x = (pos.x() - self.offset.x()) / self.scale
        y = (pos.y() - self.offset.y()) / self.scale
        return QPointF(x, y)
    
    def map_to_canvas(self, rect: QRectF):
        x = rect.left() * self.scale + self.offset.x()
        y = rect.top() * self.scale + self.offset.y()
        w = rect.width() * self.scale
        h = rect.height() * self.scale
        return QRectF(int(x), int(y), int(w), int(h))

    # click vào bbox, click ra ngoài
    def mousePressEvent(self, event):
        self.setFocus()
        if not self.pixmap:
            return
        
        pos_canvas = event.pos()
        pos_img = self.map_to_image(pos_canvas)

        if event.button() == Qt.LeftButton:

            if event.modifiers() & Qt.ControlModifier:
                self.panning = True
                self.last_pan_pos = pos_canvas
                self.setCursor(Qt.ClosedHandCursor)
                return

            # vẽ box mới
            if self.drawing:
                self.save_state()
                self.start_pos = pos_img
                self.current_rect = QRectF(pos_img, pos_img)
                self.update()
                return
            
            for idx in reversed(range(len(self.boxes))):
                rect_img = self.boxes[idx]["rect"]
                rect_canvas = self.map_to_canvas(rect_img)
                handle = self.detect_handle(pos_canvas, rect_canvas)
                
                if handle:
                    self.selected_box = idx
                    self.resize_mode = handle
                    self._real_change = False
                    self.box_selected.emit(idx)
                    cursor_map = {
                        "tl": Qt.SizeFDiagCursor,
                        "br": Qt.SizeFDiagCursor,
                        "tr": Qt.SizeBDiagCursor,
                        "bl": Qt.SizeBDiagCursor,
                    }
                    self.setCursor(cursor_map.get(handle,Qt.ArrowCursor))
                    self.update()
                    return
            idx = self.find_box_at(pos_img)
            if idx != -1:
                self.selected_box = idx
                self.dragging = True
                self._real_change = False
                self.drag_offset = pos_img - self.boxes[idx]["rect"].topLeft()
                self.box_selected.emit(idx)
                self.update_cursor(pos_canvas)
                self.update()
                return
            
            self.selected_box = None
            self.update_cursor(pos_canvas)
            self.update()
            
    # bắt đầu vẽ
    def mouseMoveEvent(self, event):
        if not self.pixmap: 
            return
        
        pos_img = self.map_to_image(event.pos())
        # resize bbox
        if self.resize_mode and self.selected_box is not None:
            if not self._real_change:
                self.save_state()
                self._real_change = True
            item = self.boxes[self.selected_box]
            r = item["rect"]
            left =  r.left()
            right = r.right()
            top = r.top()
            bottom = r.bottom()
            if self.resize_mode == "tl":
                left = pos_img.x()
                top = pos_img.y()
            elif self.resize_mode == "tr":
                right = pos_img.x()
                top = pos_img.y()
            elif self.resize_mode == "bl":
                left = pos_img.x()
                bottom = pos_img.y()
            elif self.resize_mode == "br":
                right = pos_img.x()
                bottom = pos_img.y()

            item["rect"] = QRectF(QPointF(left, top), QPointF(right, bottom)).normalized()
            self.update()
            return

        if self.panning and (event.buttons() & Qt.LeftButton) and (event.modifiers() & Qt.ControlModifier):
            delta = event.pos() - self.last_pan_pos
            self.offset += delta
            self.last_pan_pos = event.pos()
            self.clamp_offset()
            self.update()
            return
        # draw existing box
        if self.dragging and self.selected_box is not None and self.selected_box < len(self.boxes):
            if not self._real_change:
                self.save_state()
                self._real_change = True
            item = self.boxes[self.selected_box]
            r = item["rect"]
            new_top_left = pos_img - self.drag_offset
            item["rect"] = QRectF(
                new_top_left,
                QSizeF(r.width(), r.height())
            )
            self.update()
            return

        # draw new bbox realtime
        if self.start_pos is not None:
            self.current_rect = QRectF(self.start_pos, pos_img).normalized()
            self.update()
            return
        
        #detect handle hover -> update cursor
        hover_idx = self.find_box_at(pos_img)
        if hover_idx != -1:
            rect_img = self.boxes[hover_idx]['rect']
            rect_canvas = self.map_to_canvas(rect_img)
            handle = self.detect_handle(event.pos(), rect_canvas)
            if handle:
                if handle in ("tl", "br"):
                    self.setCursor(Qt.SizeFDiagCursor)
                elif handle in ("tr", "bl"):
                    self.setCursor(Qt.SizeBDiagCursor)
                return
            else:
                self.setCursor(Qt.OpenHandCursor)
                return
        self.update_cursor(event.pos())

    # event ket thuc 
    def mouseReleaseEvent(self, event):
        was_dragging = self.dragging
        was_resizing = self.resize_mode is not None

        self.resize_mode = None
        self.dragging = False

        if event.button() == Qt.MiddleButton:
            self.panning = False
            self.setCursor(Qt.ArrowCursor)

        if self.panning:
            self.panning = False
            self.setCursor(Qt.ArrowCursor)

        if (was_dragging or was_resizing) and self._real_change:
            self.boxes_changed.emit()
        self._real_change = False

        if self.current_rect:
            self.save_state()
            rect = self.current_rect.normalized()
            self.box_created.emit(rect)

        self.current_rect = None
        self.start_pos = None
        self.drawing = False
        self.update_cursor(event.pos())
        self.update()

    def mouseDoubleClickEvent(self, event):
        if not self.pixmap:
            return
        pos_img = self.map_to_image(event.pos())
        idx = self.find_box_at(pos_img)
        if idx != -1:
            self.box_double_clicked.emit(idx)

        event.accept()

    def fit_to_window(self):
        if not self.pixmap:
            return
        
        self.scale = self.fit_scale()
        self.pan_offset = QPoint(0,0)
        self.update()

    def set_hidden_labels(self, hidden_ids):
        self.hidden_labels = set(hidden_ids)
        if self.selected_box is not None:
            if self.boxes[self.selected_box]["label"] in self.hidden_labels:
                self.selected_box = None
        self.update()

    def keyPressEvent(self, event):
        if event.modifiers() & Qt.ControlModifier:
            if event.key() == Qt.Key_Z:
                self.undo()
            elif event.key() == Qt.Key_Y:
                self.redo()

            if event.key() == Qt.Key_0:
                self.fit_to_window()
                event.accept()
                return

            elif event.key() == Qt.Key_Plus or event.key() == Qt.Key_Equal:
                self.zoom_in()
                event.accept()
                return

            elif event.key() == Qt.Key_Minus:
                self.zoom_out()
                event.accept()
                return
            
        if event.key() == Qt.Key_W:
            self.drawing = True
            if self.current_label is not None:
                self.set_label_cursor(self.current_label)
            else:
                self.setCursor(Qt.CrossCursor)
            return  
        if event.key() == Qt.Key_Escape:
            self.drawing = False
            self.setCursor(Qt.ArrowCursor)
        
        if event.key() == Qt.Key_Delete:
            if self.selected_box is not None:
                if 0 <= self.selected_box < len(self.boxes):
                    del self.boxes[self.selected_box]
                    self.boxes_changed.emit()
                self.selected_box = None
                self.unsetCursor()
                self.update()
                log.info(f"Delete bbox index={self.selected_box}")
                return
        
        if event.key() == Qt.Key_D:
            self.key_next_pressed.emit()
        elif event.key() == Qt.Key_A:
            self.key_prev_pressed.emit()
        super().keyPressEvent(event)

    # vẽ 4 điểm góc
    def draw_handles(self, painter, rect, color):
        size = max(6, int(8 / self.scale))
        half = size / 2
        painter.setBrush(color)
        painter.setPen(Qt.NoPen)
        points = [
            rect.topLeft(),
            rect.topRight(),
            rect.bottomLeft(),
            rect.bottomRight()
        ]
        for p in points:
            handle_rect = QRectF(
                p.x() - half,
                p.y() - half,
                size,
                size
            )
            painter.drawRect(handle_rect)

    # handle thay doi 4 diem goc phong to, thu nho
    def detect_handle(self, pos_canvas: QPointF, rect_canvas: QRectF): 
        size = max(6, int(8 / self.scale))
        handles = {
            "tl": QRectF(
                rect_canvas.left() - size / 2,
                rect_canvas.top() - size / 2,
                size,
                size
            ),
            "tr": QRectF(
                rect_canvas.right() - size / 2,
                rect_canvas.top() - size / 2,
                size,
                size
            ),
            "bl": QRectF(
                rect_canvas.left() - size / 2,
                rect_canvas.bottom() - size / 2,
                size,
                size
            ),
            "br": QRectF(
                rect_canvas.right() - size / 2,
                rect_canvas.bottom() - size / 2,
                size,
                size
            ),
        }

        for name, rect in handles.items():
            if rect.contains(pos_canvas):
                return name
        return None

    # detect click bbox
    def find_box_at(self, pos_img):
        for item in range(len(self.boxes) -1, -1, -1):
            rect = self.boxes[item]["rect"]
            if rect.contains(pos_img):
                return item
        return -1

    # ctrl zoom in, zoom out
    def wheelEvent(self, event):
        if not self.pixmap:
            return
        if event.modifiers() & Qt.ControlModifier:
            mouse_pos = QPointF(event.pos())
            old_pos = self.map_to_image_f(mouse_pos)
            zoom_factor = 1.25
            min_scale = self.fit_scale()
            max_scale = min_scale * 20   # đồng bộ giới hạn zoom tối đa với _zoom_around_center

            if event.angleDelta().y() > 0:
                new_scale = self.scale * zoom_factor
                if new_scale >= max_scale:
                    self.scale = max_scale
                else:
                    self.scale = new_scale
            else:
                new_scale = self.scale / zoom_factor
                if new_scale <= min_scale:
                    self.scale = min_scale
                    self.center_image()
                    self.update()
                    return
                else:
                    self.scale = new_scale

            new_offset_x = mouse_pos.x() - old_pos.x() * self.scale
            new_offset_y = mouse_pos.y() - old_pos.y() * self.scale
            self.offset = QPointF(new_offset_x, new_offset_y)
            self.clamp_offset()
            self.update()

    def zoom_in(self):
        self._zoom_around_center(1.25)

    def zoom_out(self):
        self._zoom_around_center(1 / 1.25)

    def _zoom_around_center(self, factor):
        """Zoom neo theo tâm canvas - dùng chung cho nút bấm/menu/phím tắt +/-,
        cùng cơ chế giữ-điểm-neo như wheelEvent để trải nghiệm nhất quán."""
        if not self.pixmap:
            return
        center = QPointF(self.width() / 2, self.height() / 2)
        anchor_img = self.map_to_image_f(center)
        min_scale = self.fit_scale()
        max_scale = min_scale * 20   # giới hạn zoom tối đa 20x so với fit-to-window
        new_scale = self.scale * factor
        new_scale = max(min_scale, min(new_scale, max_scale))
        if new_scale == self.scale:
            return
        self.scale = new_scale
        if self.scale <= min_scale:
            self.center_image()
        else:
            self.offset = QPointF(
                center.x() - anchor_img.x() * self.scale,
                center.y() - anchor_img.y() * self.scale
            )
            self.clamp_offset()
        self.update()

    def set_label(self, label_id):
        self.current_label = label_id
        
    # color label
    def get_label_color(self, label_id):
        hue = (label_id * 47) % 360
        color = QColor()
        color.setHsv(hue, 160, 235)
        return color
    # caculator color text constrast
    def get_contrast_text_color(self, bg_color):
        luminance = 0.299 * bg_color.red() + 0.587 * bg_color.green() + 0.114 * bg_color.blue()
        return QColor(Qt.black) if luminance > 150 else QColor(Qt.white)
    
    #cursor màu
    def set_label_cursor(self, label_id):
        color = self.get_label_color(label_id)
        pixmap = QPixmap(16, 16)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        pen = QPen(color)
        pen.setWidth(2)
        painter.setPen(pen)
        # vẽ dấu +
        painter.drawLine(8, 0, 8, 16)
        painter.drawLine(0, 8, 16, 8)
        painter.end()
        self.setCursor(QCursor(pixmap))

    # update cursor handle resize
    def update_cursor_for_hanle(self, handle):
        if handle in ("tl", "br"):
            self.setCursor(Qt.SizeFDiagCursor)
        elif handle in ("tr", "bl"):
            self.setCursor(Qt.SizeBDiagCursor)
        else:
            self.setCursor(Qt.ArrowCursor)
    # resize auto scale
    def resizeEvent(self, event):
        if self.pixmap:
            if self.scale <= self.fit_scale():
                self.fit_to_window()
        self.update()

    # update cursor
    def update_cursor(self, pos_canvas):
        if not self.pixmap:
            self.setCursor(Qt.ArrowCursor)
            return
        #1: resize mode
        if self.resize_mode:
            if self.resize_mode in ("tl", "br"):
                self.setCursor(Qt.SizeFDiagCursor)
            else:
                self.setCursor(Qt.SizeBDiagCursor)
            return
        #2: drawing mode
        if self.drawing:
            self.setCursor(Qt.CrossCursor)
            return
        #3: panning
        if self.panning:
            self.setCursor(Qt.ClosedHandCursor)
            return
        #4: hover bbox
        pos_img = self.map_to_image(pos_canvas)
        idx = self.find_box_at(pos_img)
        if idx!= -1:
            self.setCursor(Qt.OpenHandCursor)
            return
        self.setCursor(Qt.ArrowCursor)
    
    def fit_scale(self):
        if not self.pixmap:
            return 1.0
        return min(
            self.width() / self.pixmap.width(),
            self.height() / self.pixmap.height()
        )
    
    def clamp_offset(self):
        if not self.pixmap:
            return
        scaled_w = self.pixmap.width() * self.scale
        scaled_h = self.pixmap.height() * self.scale
        min_x = self.width() - scaled_w
        min_y = self.height() - scaled_h
        max_x = 0
        max_y = 0
        self.offset.setX(max(min_x, min(self.offset.x(), max_x)))
        self.offset.setY(max(min_y, min(self.offset.y(), max_y)))
    
    def center_image(self):
        if not self.pixmap:
            return
        scaled_w = self.pixmap.width() * self.scale
        scaled_h = self.pixmap.height() * self.scale
        canvas_w = self.width()
        canvas_h = self.height()
        self.offset = QPointF(
            (canvas_w - scaled_w) / 2,
            (canvas_h - scaled_h) / 2
        )

    def clone_boxes(self):
        return[
            {
                "rect": QRectF(box["rect"]),
                "label": box["label"],
                "label_name": box.get("label_name", "")
            }
            for box in self.boxes
        ]
    def save_state(self):
        self.undo_stack.append(self.clone_boxes())
        if len(self.undo_stack) > 100:
            self.undo_stack.pop(0)
        self.redo_stack.clear()
    def undo(self):
        if not self.undo_stack:
            return
        self.redo_stack.append(self.clone_boxes())
        self.boxes = self.undo_stack.pop()
        self.selected_box = None
        self.update()
        self.boxes_changed.emit()
    def redo(self):
        if not self.redo_stack:
            return
        self.undo_stack.append(self.clone_boxes())
        self.boxes = self.redo_stack.pop()
        self.selected_box = None
        self.update()
        self.boxes_changed.emit()