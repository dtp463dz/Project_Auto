from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QPen, QPixmap, QImage
from PyQt5.QtCore import Qt, QRect
import cv2

class ImageCanvas(QWidget):
    def __init__(self):
        super().__init__()
        self.pixmap = None
        self.scale = 1.0
        self.boxes = []
        self.current_rect = None
        self.start_pos = None
        self.setMouseTracking(True)

    def load_image(self, path):
        self.pixmap = QPixmap(path)
        self.scale = 1.0
        self.boxes.clear()
        self.update()
    
    def show_image(self, path, label):
        img = cv2.imread(path)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        h, w, ch = img.shape
        qt_img = QImage(img.data, w, h, ch*w, QImage.Format.Format_RGB888)
        pix = QPixmap.fromImage(qt_img)
        pix = pix.scaled(label.width(), label.height(), Qt.AspectRatioMode.KeepAspectRatio)
        label.setPixmap(pix)

    def paintEvent(self, event):
        if not self.pixmap:
            return

        painter = QPainter(self)
        painter.scale(self.scale, self.scale)
        painter.drawPixmap(0, 0, self.pixmap)
        pen = QPen(Qt.red, 2)
        painter.setPen(pen)

        for box in self.boxes:
            painter.drawRect(box)

        if self.current_rect:
            painter.drawRect(self.current_rect)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.start_pos = event.pos() / self.scale


    def mouseMoveEvent(self, event):
        if self.start_pos:
            end = event.pos() / self.scale
            self.current_rect = QRect(self.start_pos.toPoint(), end.toPoint())
            self.update()

    def mouseReleaseEvent(self, event):
        if self.current_rect:
            self.boxes.append(self.current_rect.normalized())
        self.current_rect = None
        self.start_pos = None
        self.update()

    def wheelEvent(self, event):
        if event.angleDelta().y() > 0:
            self.zoom_in()
        else:
            self.zoom_out()

    def zoom_in(self):
        self.scale *= 1.1
        self.update()

    def zoom_out(self):
        self.scale /= 1.1
        self.update()