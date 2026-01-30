from PyQt5.QtWidgets import QDialog, QVBoxLayout, QListWidget, QPushButton, QHBoxLayout, QInputDialog

class SelectLabelDialog(QDialog):
    def __init__(self, labels):
        super().__init__()
        self.setWindowTitle("Select Label")
        self.resize(300, 400)
        self.selected_label = None
        layout = QVBoxLayout(self)
        self.list_widget = QListWidget()
        self.list_widget.addItems(labels)
        btn_new = QPushButton("New Label")
        btn_ok = QPushButton("OK")
        btn_cancel = QPushButton("Cancel")

        btn_new.clicked.connect(self.create_label)
        btn_ok.clicked.connect(self.accept_label)
        btn_cancel.clicked.connect(self.reject)

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(btn_new)
        btn_layout.addWidget(btn_ok)
        btn_layout.addWidget(btn_cancel)

        layout.addWidget(self.list_widget)
        layout.addLayout(btn_layout)

    def create_label(self):
        text, ok = QInputDialog.getText(
            self, "New Label", "Label name:"
        )
        if ok and text.strip():
            self.list_widget.addItem(text.strip())

    def accept_label(self):
        item = self.list_widget.currentItem()
        if item:
            self.selected_label = item.text()
            self.accept()
