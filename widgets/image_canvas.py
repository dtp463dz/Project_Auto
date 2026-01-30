from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QPen, QPixmap, QColor
from PyQt5.QtCore import Qt, QRect, QPoint, pyqtSignal
import colorsys

class ImageCanvas(QWidget):
    box_created = pyqtSignal(QRect)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.pixmap = None
        self.scale = 1.0
        self.boxes = []
        # self.drawing = False
        self.current_label = None
        self.current_rect = None
        self.start_pos = None
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
            label_name = item.get("label_name", "")

            pen = QPen(self.get_label_color(label_id), 2)
            painter.setPen(pen)
            canvas_rect = self.map_to_canvas(rect)
            painter.drawRect(canvas_rect)
            if label_name:
                painter.drawText(canvas_rect.topLeft() + QPoint(3, -3), label_name)

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

    def mousePressEvent(self, event):
        self.setFocus()
        if not self.pixmap:
            return
        # if not self.drawing:
        #     return

        if event.button() == Qt.LeftButton:
            self.start_pos = self.map_to_image(event.pos())

    def mouseMoveEvent(self, event):
        if self.start_pos:
            end = self.map_to_image(event.pos())
            self.current_rect = QRect(self.start_pos, end)
            self.update()

    def mouseReleaseEvent(self, event):
        if self.current_rect:
            rect = self.current_rect.normalized()
            self.box_created.emit(rect)

        self.current_rect = None
        self.start_pos = None
        # self.drawing = False
        self.update()

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
        print("KEY:", event.key())
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
            # self.drawing = True
            print("CREATE BOX MODE")
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