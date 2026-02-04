from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QPushButton

class NewLabelDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("New Label")
        self.name = None
        layout = QVBoxLayout(self)

        self.edit = QLineEdit()
        self.edit.setPlaceholderText("Label name")

        btn_ok = QPushButton("OK")
        btn_cancel = QPushButton("Cancel")

        btn_ok.clicked.connect(self.on_ok)
        btn_cancel.clicked.connect(self.reject)

        layout.addWidget(self.edit)
        layout.addWidget(btn_ok)
        layout.addWidget(btn_cancel)

    def on_ok(self):
        text = self.edit.text().strip()
        if not text:
            return 
        self.name = text
        self.accept()
