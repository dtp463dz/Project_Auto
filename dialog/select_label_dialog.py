from PyQt5.QtWidgets import QDialog, QVBoxLayout, QListWidget, QPushButton, QHBoxLayout, QInputDialog, QMessageBox

class SelectLabelDialog(QDialog):
    def __init__(self, labels, current=None):
        super().__init__()
        self.setWindowTitle("Select Label")
        self.resize(300, 400)
        self.selected_label = None
        self.selected_index = None
        self.labels = labels
        self.current = current
        layout = QVBoxLayout(self)
        self.list_widget = QListWidget()
        self.list_widget.addItems(labels)
        # chọn label hiện tại
        if current is not None and current < len(labels):
            self.list_widget.setCurrentRow(current)
        
        # button
        btn_new = QPushButton("New")
        btn_edit = QPushButton("Edit")
        btn_delete = QPushButton("Delete")
        btn_ok = QPushButton("OK")
        btn_cancel = QPushButton("Cancel")

        btn_new.clicked.connect(self.create_label)
        btn_edit.clicked.connect(self.edit_label)
        btn_delete.clicked.connect(self.delete_label)
        btn_ok.clicked.connect(self.accept_label)
        btn_cancel.clicked.connect(self.reject)

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(btn_new)
        btn_layout.addWidget(btn_edit)
        btn_layout.addWidget(btn_delete)

        btn_layout2 = QHBoxLayout()
        btn_layout2.addWidget(btn_ok)
        btn_layout2.addWidget(btn_cancel)

        layout.addWidget(self.list_widget)
        layout.addLayout(btn_layout)
        layout.addLayout(btn_layout2)


    def create_label(self):
        text, ok = QInputDialog.getText(
            self, "New Label", "Label name:"
        )
        if ok and text.strip():
            self.labels.append(text.strip())
            self.list_widget.addItem(text.strip())

    def edit_label(self):
        row = self.list_widget.currentRow()
        if row < 0:
            return
        old = self.labels[row]
        text, ok = QInputDialog.getText(
            self, "Edit Label", "Label name:", text=old
        )
        if ok and text.strip():
            self.labels[row] = text.strip()
            self.list_widget.item(row).setText(text.strip())

    def delete_label(self):
        row = self.list_widget.currentRow()
        if row < 0:
            return
        reply = QMessageBox.question(
            self,
            "Delete",
            f"Delete label '{self.labels[row]}' ?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.labels.pop(row)
            self.list_widget.takeItem(row)

    def accept_label(self):
        row = self.list_widget.currentRow()
        if row >= 0:
            self.selected_index = row
            self.selected_label = self.labels[row]
            self.accept()

    def get_result(self):
        return self.selected_index, self.selected_label
