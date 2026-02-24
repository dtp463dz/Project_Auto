from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QPen, QPixmap, QColor, QCursor
from PyQt5.QtCore import Qt, QRect, QPoint, pyqtSignal, QSize, QPointF, QRectF
import colorsys
from gui.logger import setup_logger
log = setup_logger()

class ImageCanvas(QWidget):
    box_created = pyqtSignal(QRect)
    box_double_clicked = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.pixmap = None
        self.scale = 1.0
        self.boxes = []
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
        img_w =self.pixmap.width()
        img_h = self.pixmap.height()
        canvas_w = self.width()
        canvas_h = self.height()
        
        if canvas_w == 0 or canvas_h == 0:
            self.scale = 1.0
        else: 
            self.scale = min(canvas_w / img_w, canvas_h / img_h)

        #center image
        scaled_w = img_w * self.scale
        scaled_h = img_h * self.scale
        offset_x = (canvas_w - scaled_w) / 2
        offset_y = (canvas_h - scaled_h) / 2
        self.offset = QPoint(int(offset_x), int(offset_y))

        self.boxes.clear()
        self.current_rect = None
        self.start_pos = None
        self.selected_box = None
        self.dragging = False
        self.resize_mode = None
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
    
    def map_to_canvas(self, rect):
        x = rect.x() * self.scale + self.offset.x()
        y = rect.y() * self.scale + self.offset.y()
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
            idx = self.find_box_at(pos_img)

            if idx != -1:
                self.selected_box = idx
                self.dragging = True
                self.drag_offset = pos_img - self.boxes[idx]["rect"].topLeft()
                self.current_label = self.boxes[idx]["label"]
                self.set_label_cursor(self.current_label)
                self.update()
                print("Selected box:", idx)
                return
            if idx == -1:
                self.selected_box = None
                self.panning = True
                self.last_pan_pos = event.pos()
                self.setCursor(Qt.ClosedHandCursor)
                self.update()
                return

            # vẽ box mới
            if self.drawing:
                self.start_pos = pos_img
                self.current_rect = QRect(pos_img, pos_img)
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
            if self.resize_mode == "tl":
                r.setTopLeft(pos_img)
            elif self.resize_mode == "tr":
                r.setTopRight(pos_img)
            elif self.resize_mode == "bl":
                r.setBottomLeft(pos_img)
            elif self.resize_mode == "br":
                r.setBottomRight(pos_img)

            item["rect"] = r.normalized()
            self.update()
            return

        if self.panning:
            delta = event.pos() - self.last_pan_pos
            self.offset += delta
            self.last_pan_pos = event.pos()
            self.clamp_offset()
            self.update()
            return
        # draw box
        if self.dragging and self.selected_box is not None and self.selected_box < len(self.boxes):
            item = self.boxes[self.selected_box]
            r = item["rect"]
            new_top_left = pos_img - self.drag_offset
            item["rect"] = QRect(new_top_left, r.size())
            self.update()
            return

        # draw new bbox realtime
        if self.start_pos:
            self.current_rect = QRect(self.start_pos, pos_img)
            self.update()

    # event ket thuc 
    def mouseReleaseEvent(self, event):
        self.resize_mode = None
        self.dragging = False

        if event.button() == Qt.MiddleButton:
            self.panning = False
            self.setCursor(Qt.ArrowCursor)

        if self.panning:
            self.panning = False
            self.setCursor(Qt.ArrowCursor)

        if self.current_rect:
            rect = self.current_rect.normalized()
            self.box_created.emit(rect)

        self.current_rect = None
        self.start_pos = None
        self.drawing = False
        self.setCursor(Qt.ArrowCursor)
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
        
        if event.key() == Qt.Key_Delete:
            if self.selected_box is not None:
                if 0 <= self.selected_box < len(self.boxes):
                    del self.boxes[self.selected_box]
                self.selected_box = None
                self.unsetCursor()
                self.update()
                log.info(f"Delete bbox index={self.selected_box}")
                return
        super().keyPressEvent(event)

    # vẽ 4 điểm góc
    def draw_handles(self, painter, rect, color):
        size = 4
        half = size // 2
        points = [
            rect.topLeft(),
            rect.topRight(),
            rect.bottomLeft(),
            rect.bottomRight()
        ]

        painter.setBrush(color)
        painter.setPen(QPen(color, 1))
        for p in points:
            painter.drawRect(
                p.x() - half,
                p.y() - half,
                size,
                size
            )

    # handle thay doi 4 diem goc phong to, thu nho
    def detect_handle(self, pos_canvas, rect_canvas): 
        size = 8
        handles = {
            "tl": QRect(rect_canvas.topLeft() - QPoint(size//2, size//2), QSize(size, size)),
            "tr": QRect(rect_canvas.topRight() - QPoint(size//2, size//2), QSize(size, size)),
            "bl": QRect(rect_canvas.bottomLeft() - QPoint(size//2, size//2), QSize(size, size)),
            "br": QRect(rect_canvas.bottomRight() - QPoint(size//2, size//2), QSize(size, size)),
        }

        for k, r in handles.items():
            if r.contains(pos_canvas):
                return k
        return None

    # detect click bbox
    def find_box_at(self, pos_img):
        for item in range(len(self.boxes) -1, -1, -1):
            if self.boxes[item]["rect"].contains(pos_img):
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
            max_scale = min_scale * 20

            if event.angleDelta().y() > 0:
                new_scale = self.scale * zoom_factor
                if new_scale > max_scale:
                    new_scale = max_scale
            else:
                new_scale = self.scale / zoom_factor
                if new_scale < min_scale:
                    new_scale = min_scale

            if new_scale == self.scale:
                return
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
    
    # resize auto scale
    def resizeEvent(self, event):
        
        if self.pixmap:
            if self.scale <= self.fit_scale():
                self.fit_to_window()
        self.update()
    
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
        