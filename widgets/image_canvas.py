from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QPen, QPixmap
from PyQt5.QtCore import Qt, QRect, QPoint
import cv2

class ImageCanvas(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.pixmap = None
        self.scale = 1.0
        self.boxes = []
        self.current_rect = None
        self.start_pos = None
        self.offset = QPoint(0, 0)
        self.setMouseTracking(True)

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

        pen = QPen(Qt.red, 2)
        painter.setPen(pen)

        for box in self.boxes:
            painter.drawRect(self.map_to_canvas(box))

        if self.current_rect:
            painter.drawRect(self.map_to_canvas(self.current_rect))

    def map_to_image(self, pos):
        return (pos - self.offset) / self.scale
    
    def map_to_canvas(self, rect):
        x = rect.x() * self.scale + self.offset.x()
        y = rect.y() * self.scale + self.offset.y()
        w = rect.width() * self.scale
        h = rect.height() * self.scale
        return QRect(int(x), int(y), int(w), int(h))

    def mousePressEvent(self, event):
        if not self.pixmap:
            return
        if event.button() == Qt.LeftButton:
            self.start_pos = self.map_to_image(event.pos())

    def mouseMoveEvent(self, event):
        if self.start_pos:
            end = self.map_to_image(event.pos())
            self.current_rect = QRect(self.start_pos.toPoint(), end.toPoint())
            self.update()

    def mouseReleaseEvent(self, event):
        if self.current_rect:
            self.boxes.append(self.current_rect.normalized())
        self.current_rect = None
        self.start_pos = None
        self.update()

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