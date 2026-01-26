import os
from PyQt5.QtWidgets import QFileDialog, QAction

class EditLib:

    def __init__(self, main_window):
        self.main = main_window
        self.menu = self.main.menuBar().addMenu("Edit")

        self.create_actions()

    def create_actions(self):
        self.action_undo = QAction("Undo", self.main)
        self.action_redo = QAction("Redo", self.main)

        self.action_undo.triggered.connect(self.undo)
        self.action_redo.triggered.connect(self.redo)

        self.menu.addAction(self.action_undo)
        self.menu.addAction(self.action_redo)

    def undo(self):
        print("Undo action")

    def redo(self):
        print("Redo action")
