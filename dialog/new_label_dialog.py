from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QPushButton

class NewLabelDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Create Label")
        self.name = None
        layout = QVBoxLayout(self)

        self.input = QLineEdit()
        self.input.setPlaceholderText("Label name")

        btn = QPushButton("Create")
        btn.clicked.connect(self.accept_label)
        layout.addWidget(self.input)
        layout.addWidget(btn)

    def accept_label(self):
        text = self.input.text().strip()
        if text: 
            self.name = text
            self.accept()
