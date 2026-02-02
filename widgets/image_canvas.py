from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QPen, QPixmap, QColor
from PyQt5.QtCore import Qt, QRect, QPoint, pyqtSignal, QSize
import colorsys

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

        self.boxes.clear()
        self.current_rect = None
        self.start_pos = None
        self.offset = QPoint(0, 0)
        self.update()

    def paintEvent(self, event):
        if not self.pixmap:
            return

        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)
        scaled = self.pixmap.scaled(
            self.pixmap.size() * self.scale,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        x = (self.width() - scaled.width()) // 2
        y = (self.height() - scaled.height()) // 2
        self.offset = QPoint(x, y)
        painter.drawPixmap(x, y, scaled)

        for item in self.boxes:
            rect = item["rect"]
            label_id = item["label"]
            label_name = str(item.get("label_name", ""))
            canvas_rect = self.map_to_canvas(rect)
            painter.setBrush(Qt.NoBrush)
            if item.get("selected"):
                pen = QPen(Qt.cyan, 2, Qt.DashLine)
            else:
                pen = QPen(self.get_label_color(label_id), 2)

            painter.setPen(pen)
            painter.drawRect(canvas_rect)
            if label_name:
                painter.drawText(canvas_rect.topLeft() + QPoint(3, -3), label_name)

            if item.get("selected"):
                self.draw_handles(painter, canvas_rect)

        # drawing bbox(realtime)
        if self.current_rect: 
            canvas_rect = self.map_to_canvas(self.current_rect.normalized())
            pen = QPen(Qt.yellow, 2, Qt.DashLine)
            painter.setPen(pen)
            painter.drawRect(canvas_rect)
            self.draw_handles(painter, canvas_rect)
    

    def map_to_image(self, pos):
        x = (pos.x() - self.offset.x()) / self.scale
        y = (pos.y() - self.offset.y()) / self.scale
        return QPoint(int(x), int(y))
    
    def map_to_canvas(self, rect):
        x = rect.x() * self.scale + self.offset.x()
        y = rect.y() * self.scale + self.offset.y()
        w = rect.width() * self.scale
        h = rect.height() * self.scale
        return QRect(int(x), int(y), int(w), int(h))

    # click vào bbox, click ra ngoài
    def mousePressEvent(self, event):
        self.setFocus()
        if not self.pixmap:
            return
        
        pos_canvas = event.pos()
        pos_img = self.map_to_image(pos_canvas)

        if event.button() == Qt.LeftButton:
            if self.selected_box is not None:
                if self.selected_box >= len(self.boxes):
                    self.selected_box = None
                else:
                    item = self.boxes[self.selected_box]
                    rect_canvas = self.map_to_canvas(item["rect"])
                    handle = self.detect_handle(pos_canvas, rect_canvas)
                    if handle:
                        self.resize_mode=handle
                        return

            # ưu tiên select box 
            idx = self.find_box_at(pos_img)
            if idx != -1:
                self.selected_box = idx
                for b in self.boxes:
                    b["selected"] = False
                self.boxes[idx]["selected"] = True
                self.dragging = True
                self.drag_offset = pos_img - self.boxes[idx]["rect"].topLeft()
                self.setCursor(Qt.SizeAllCursor)
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

        # draw box
        if self.dragging and self.selected_box is not None:
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
        if self.resize_mode:
            self.resize_mode = None
            return

        if self.dragging:
            self.dragging = False
            return

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
        
        img_w =self.pixmap.width()
        img_h = self.pixmap.height()

        canvas_w = self.width()
        canvas_h = self.height()
        self.scale = min(
            canvas_w / img_w,
            canvas_h / img_h
        )
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
            self.setCursor(Qt.CrossCursor)
            print("LABEL MODE")
            return    
        
        if event.key() == Qt.Key_Delete:
            if self.selected_box is not None:
                if 0 <= self.selected_box < len(self.boxes):
                    del self.boxes[self.selected_box]
                self.selected_box = None
                self.unsetCursor()
                self.update()
                return
        super().keyPressEvent(event)

    # vẽ 4 điểm góc
    def draw_handles(self, painter, rect):
        size = 6
        half = size // 2
        points = [
            rect.topLeft(),
            rect.topRight(),
            rect.bottomLeft(),
            rect.bottomRight()
        ]

        painter.setBrush(QColor(255, 255, 255))
        painter.setPen(QPen(Qt.black, 1))
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
        modifiers = event.modifiers()
        if modifiers & Qt.ControlModifier:
            if event.angleDelta().y() > 0:
                self.zoom_in()
            else:
                self.zoom_out()
        else: 
            event.ignore()

    def zoom_in(self):
        self.scale *= 1.1
        self.update()

    def zoom_out(self):
        self.scale /= 1.1
        self.update()

    def set_label(self, label_id):
        self.current_label = label_id
        
    def get_label_color(self, label_id):
        hue = (label_id * 37) % 360
        color = QColor()
        color.setHsv(hue, 255, 200)
        return color