import qtawesome as qta
from PyQt5.QtWidgets import QApplication, QPushButton

app = QApplication([])

# Tạo icon "vô cùng đơn giản" bằng tên
icon = qta.icon('fa5s.thumbs-up', color='blue')

button = QPushButton(" Like")
button.setIcon(icon)
button.show()

app.exec_()