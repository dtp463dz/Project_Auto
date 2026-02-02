from PyQt5.QtWidgets import QDialog, QVBoxLayout, QListWidget, QPushButton, QHBoxLayout, QInputDialog, QMessageBox

class SelectLabelDialog(QDialog):
    def __init__(self, labels, current=None):
        super().__init__()
        self.setWindowTitle("Select Label")
        self.resize(300, 400)
        # self.selected_label = None
        # self.selected_index = None
        self.labels = labels
        self.dialog_action = None
        self.dialog_data = None

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

        btn_new.clicked.connect(self.new_label)
        btn_edit.clicked.connect(self.edit_label)
        btn_delete.clicked.connect(self.delete_label)
        btn_ok.clicked.connect(self.select_label)
        btn_cancel.clicked.connect(self.reject)

        row1 = QHBoxLayout()
        row1.addWidget(btn_new)
        row1.addWidget(btn_edit)
        row1.addWidget(btn_delete)

        row2 = QHBoxLayout()
        row2.addWidget(btn_ok)
        row2.addWidget(btn_cancel)

        layout.addWidget(self.list_widget)
        layout.addLayout(row1)
        layout.addLayout(row2)

    def new_label(self):
        text, ok = QInputDialog.getText(
            self, "New Label", "Label name:"
        )
        if ok and text.strip():
            name = text.strip()
            if name in self.labels:
                return
            
            # hien thi trong dialog
            self.list_widget.addItem(name)
            self.list_widget.setCurrentRow(self.list_widget.count() - 1)

            self.dialog_action = "new"
            self.dialog_data = name
            self.accept()

    def edit_label(self):
        row = self.list_widget.currentRow()
        if row < 0:
            return
        old = self.labels[row]
        text, ok = QInputDialog.getText(
            self, "Edit Label", "Label name:", text=old
        )
        new_name = text.strip()
        if not ok or not new_name:
            return 
        if new_name in self.labels and new_name != old:
            QMessageBox.warning(
                self,
                "Duplicate label",
                f"Label '{new_name}' already exists."
            )
            return
        self.dialog_action = "edit"
        self.dialog_data = (row, text.strip())
        self.accept()

    def delete_label(self):
        row = self.list_widget.currentRow()
        if row < 0:
            return
        reply = QMessageBox.question(
            self,
            "Delete Label",
            f"Delete '{self.labels[row]}' ?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.dialog_action = "delete"
            self.dialog_data = row
            self.accept()

    def select_label(self):
        row = self.list_widget.currentRow()
        if row >= 0:
            self.dialog_action = "select"
            # self.dialog_data = self.list_widget.item(row).text()
            self.dialog_data = int(row)
            self.accept()

    def get_result(self):
        return self.dialog_action, self.dialog_data
