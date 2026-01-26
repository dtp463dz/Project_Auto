from PyQt5.QtWidgets import QAction, QMessageBox


class HelpLib:
    def __init__(self, main_window):
        self.main = main_window
        self.menu = self.main.menuBar().addMenu("Help")

        self.create_actions()

    def create_actions(self):
        self.about_action = QAction("About TPLabel", self.main)
        self.about_action.triggered.connect(self.show_about)

        self.menu.addAction(self.about_action)

    def show_about(self):
        QMessageBox.information(
            self.main,
            "About",
            "TPLabel\nIndustrial Labeling Tool\nVersion 1.0"
        )
