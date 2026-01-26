from PyQt5.QtWidgets import QAction


class ViewLib:
    def __init__(self, main_window):
        self.main = main_window
        self.menu = self.main.menuBar().addMenu("View")

        self.view_actions()
       

    def view_actions(self):
        self.action_zoom_in = QAction("Zoom In", self.main)
        self.action_zoom_out = QAction("Zoom Out", self.main)

        self.action_zoom_in.triggered.connect(self.zoom_in)
        self.action_zoom_out.triggered.connect(self.zoom_out)

        self.menu.addAction(self.action_zoom_in)
        self.menu.addAction(self.action_zoom_out)

    def zoom_in(self):
        print("Zoom In action")

    def zoom_out(self):
        print("Zoom Out action")
