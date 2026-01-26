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

        self.open_ok_action.triggered.connect(self.open_ok_menu)
        self.open_ng_action.triggered.connect(self.open_ng_menu)
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
    
    def open_ok_menu(self):
        folder = self.open_folder("Select OK Folder")
        if folder:
            self.main.ok_images = self.load_images(folder)
            if self.main.ok_images:
                self.main.show_image(self.main.ok_images[0], self.main.ok_label)

    def open_ng_menu(self):
        folder = self.open_folder("Select NG Folder")
        if folder:
            self.main.ng_images = self.load_images(folder)
            if self.main.ng_images:
                self.main.show_image(self.main.ng_images[0], self.main.ng_label)