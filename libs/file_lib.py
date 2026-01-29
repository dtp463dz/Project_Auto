import os
from PyQt5.QtWidgets import QFileDialog, QAction
class FileLib:

    IMAGE_EXTS = (".jpg", ".jpeg", ".png", ".bmp")

    def __init__(self, main_window):
        self.main = main_window
        self.menu = self.main.menuBar().addMenu("File")
        self.create_actions()

    def create_actions(self):
        self.open_ok_action = QAction("Open OK Folder", self.main)
        self.open_ng_action = QAction("Open NG Folder", self.main)
        self.exit_action = QAction("Exit", self.main)

        self.open_ok_action.triggered.connect(self.open_ok_folder)
        self.open_ng_action.triggered.connect(self.open_ng_folder)
        self.exit_action.triggered.connect(self.main.close)

        self.menu.addAction(self.open_ok_action)
        self.menu.addAction(self.open_ng_action)
        self.menu.addSeparator()
        self.menu.addAction(self.exit_action)

    def open_folder(self, title):
        return QFileDialog.getExistingDirectory(self.main, title)

    def load_images(self, folder):
        if not folder:
            return []
        return sorted(
            os.path.join(folder, f)
            for f in os.listdir(folder)
            if f.lower().endswith(self.IMAGE_EXTS)
        )
    
    def open_ok_folder(self):
        self.main.select_ok_folder()

    def open_ng_folder(self):
        self.main.select_ng_folder()