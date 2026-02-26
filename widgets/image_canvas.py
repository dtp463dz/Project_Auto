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
        
        painter.translate(self.offset)
        painter.scale(self.scale, self.scale)

        painter.drawPixmap(0, 0, self.pixmap)

        for idx, item in enumerate(self.boxes):
            rect = item["rect"]
            label_id = item["label"]
            label_name = str(item.get("label_name", ""))
            # canvas_rect = self.map_to_canvas(rect)
            color = self.get_label_color(label_id)
            if self.selected_box == idx: 
                pen = QPen(Qt.white, 2 / self.scale)
                fill = QColor(color)
                fill.setAlpha(120)
            else:
                pen = QPen(color, 1 / self.scale)
                fill = QColor(color)
                fill.setAlpha(40)
            
            pen.setCosmetic(False)
            painter.setPen(pen)
            painter.setBrush(fill)
            painter.drawRect(rect)
            if self.selected_box == idx:
                self.draw_handles(painter, rect, color)

            if label_name:
                painter.drawText(rect.topLeft() + QPointF(3 / self.scale, -3 / self.scale), label_name)

        # drawing bbox(realtime)
        if self.current_rect: 
            rect = self.current_rect.normalized()
            if self.current_label is not None:
                color = self.get_label_color(self.current_label)
            else:
                color = Qt.red
            pen = QPen(color, 1 / self.scale)
            painter.setPen(pen)
            painter.drawRect(rect)
            self.draw_handles(painter, rect, color)
    

    def map_to_image(self, pos):
        x = (pos.x() - self.offset.x()) / self.scale
        y = (pos.y() - self.offset.y()) / self.scale
        return QPoint(int(x), int(y))
    
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
                    # resize mode
                    self.save_state()
                    self.selected_box = idx
                    self.resize_mode = handle
                    cursor_map = {
                        "tl": Qt.SizeFDiagCursor,
                        "br": Qt.SizeFDiagCursor,
                        "tr": Qt.SizeBDiagCursor,
                        "bl": Qt.SizeBDiagCursor,
                    }
                    self.setCursor(cursor_map.get(handle,Qt.ArrowCursor))
                    return
            idx = self.find_box_at(pos_img)
            if idx != -1:
                self.save_state()
                self.selected_box = idx
                self.box_selected.emit(idx)
                self.dragging = True
                self.drag_offset = pos_img - self.boxes[idx]["rect"].topLeft()
                self.update_cursor(pos_canvas)
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
        if was_dragging or was_resizing:
            self.boxes_changed.emit()

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
            print("Label Mode")
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
            mouse_pos = event.pos()
            old_pos = self.map_to_image(mouse_pos)
            zoom_factor = 1.25
            min_scale = self.fit_scale()

            if event.angleDelta().y() > 0:
                self.scale *= zoom_factor
                
            else:
                new_scale = self.scale / zoom_factor
                if new_scale <= min_scale:
                    self.scale = min_scale
                    self.center_image()
                    self.update()
                    return
                else:
                    self.scale = new_scale
            
            new_pos = self.map_to_image(mouse_pos)
            delta = new_pos - old_pos
            self.offset += QPointF(
                delta.x() * self.scale,
                delta.y() * self.scale
            )
            self.clamp_offset()
            self.update()

    def zoom_in(self):
        self.scale *= 1.1
        self.update()

    def zoom_out(self):
        if not self.pixmap:
            return
        min_scale = self.fit_scale()
        new_scale = self.scale * 0.9
        if new_scale < min_scale:
            new_scale = min_scale
        if new_scale == self.scale:
            return
        self.scale = new_scale
        if self.scale == min_scale:
            self.pan_offset = QPoint(0, 0)

        self.update()

    def set_label(self, label_id):
        self.current_label = label_id
        
    def get_label_color(self, label_id):
        hue = (label_id * 37) % 360
        color = QColor()
        color.setHsv(hue, 255, 200)
        return color
    
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
                "label": box["label"]
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
        self.update()
        self.boxes_changed.emit()
    def redo(self):
        if not self.redo_stack:
            return
        self.undo_stack.append(self.clone_boxes())
        self.boxes = self.redo_stack.pop()
        self.update()
        self.boxes_changed.emit()