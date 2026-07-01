LIGHT_QSS = """
QMainWindow {
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:1,
        stop:0 #F5F8FC,
        stop:0.5 #EEF3FA,
        stop:1 #E4ECF7
    );
    font-family: "Segoe UI";
    font-size: 13px;
    color: #1F2937;
}

QWidget#rightPanel {
    background: qlineargradient(
        x1:0, y1:0, x2:0, y2:1,
        stop:0 #FFFFFF,
        stop:1 #F1F5FB
    );
    border-left: 1px solid #DCE3EE;
}

QLabel {
    color: #33415C;
}

QPushButton {
    background: qlineargradient(
        x1:0, y1:0, x2:0, y2:1,
        stop:0 #5B9CF0,
        stop:1 #4A90E2
    );
    color: white;
    border: none;
    border-radius: 6px;
    padding: 6px 14px;
}

QPushButton:hover {
    background: qlineargradient(
        x1:0, y1:0, x2:0, y2:1,
        stop:0 #79B2FF,
        stop:1 #6AAEFF
    );
}

QPushButton:pressed {
    background: #357ABD;
}

QPushButton:checked {
    background: qlineargradient(
        x1:0, y1:0, x2:0, y2:1,
        stop:0 #2F6FBF,
        stop:1 #245A9C
    );
}

QListWidget {
    background-color: #FFFFFF;
    border: 1px solid #DCE3EE;
    border-radius: 6px;
    padding: 4px;
    outline: none;
}

QListWidget::item {
    padding: 4px 6px;
    border-radius: 4px;
}

QListWidget::item:selected {
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 #CFE2FF,
        stop:1 #BBD6FF
    );
    color: #14213D;
}

QListWidget::item:hover {
    background-color: #EAF1FD;
}

QStatusBar {
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 #EEF3FA,
        stop:1 #E4ECF7
    );
    border-top: 1px solid #DCE3EE;
    color: #33415C;
}

QScrollBar:vertical {
    background: transparent;
    width: 10px;
}
QScrollBar::handle:vertical {
    background: #C3D2E8;
    border-radius: 5px;
    min-height: 24px;
}
QMenuBar {
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 #EEF3FA,
        stop:1 #E4ECF7
    );
    color: #1F2937;
    border-bottom: 1px solid #DCE3EE;
    padding: 2px;
}

QMenuBar::item {
    background: transparent;
    padding: 4px 10px;
    border-radius: 4px;
}

QMenuBar::item:selected {
    background-color: #CFE2FF;
    color: #14213D;
}

QMenu {
    background-color: #FFFFFF;
    border: 1px solid #DCE3EE;
    color: #1F2937;
    padding: 4px;
}

QMenu::item {
    padding: 5px 24px 5px 12px;
    border-radius: 4px;
}

QMenu::item:selected {
    background-color: #CFE2FF;
    color: #14213D;
}

QMenu::separator {
    height: 1px;
    background: #DCE3EE;
    margin: 4px 6px;
}

QMessageBox {
    background-color: #FFFFFF;
    color: #1F2937;
}

QMessageBox QLabel {
    color: #1F2937;
}
"""

DARK_QSS = """
QMainWindow {
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:1,
        stop:0 #1B1E2B,
        stop:0.5 #20243A,
        stop:1 #262B45
    );
    font-family: "Segoe UI";
    font-size: 13px;
    color: #E4E8F1;
}

QWidget#rightPanel {
    background: qlineargradient(
        x1:0, y1:0, x2:0, y2:1,
        stop:0 #21253A,
        stop:1 #1A1D2C
    );
    border-left: 1px solid #333A56;
}

QLabel {
    color: #C9D1E5;
}

QPushButton {
    background: qlineargradient(
        x1:0, y1:0, x2:0, y2:1,
        stop:0 #6C7BFF,
        stop:1 #5566E8
    );
    color: white;
    border: none;
    border-radius: 6px;
    padding: 6px 14px;
}

QPushButton:hover {
    background: qlineargradient(
        x1:0, y1:0, x2:0, y2:1,
        stop:0 #8390FF,
        stop:1 #6C7BFF
    );
}

QPushButton:pressed {
    background: #4451C4;
}

QPushButton:checked {
    background: qlineargradient(
        x1:0, y1:0, x2:0, y2:1,
        stop:0 #3E4BB0,
        stop:1 #313C8C
    );
}

QListWidget {
    background-color: #1E2233;
    border: 1px solid #333A56;
    border-radius: 6px;
    padding: 4px;
    color: #E4E8F1;
    outline: none;
}

QListWidget::item {
    padding: 4px 6px;
    border-radius: 4px;
}

QListWidget::item:selected {
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 #3E4BB0,
        stop:1 #4C5AD0
    );
    color: #FFFFFF;
}

QListWidget::item:hover {
    background-color: #2A2F47;
}

QStatusBar {
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 #20243A,
        stop:1 #262B45
    );
    border-top: 1px solid #333A56;
    color: #C9D1E5;
}

QScrollBar:vertical {
    background: transparent;
    width: 10px;
}
QScrollBar::handle:vertical {
    background: #3A4066;
    border-radius: 5px;
    min-height: 24px;
}
QMenuBar {
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 #20243A,
        stop:1 #262B45
    );
    color: #E4E8F1;
    border-bottom: 1px solid #333A56;
    padding: 2px;
}

QMenuBar::item {
    background: transparent;
    padding: 4px 10px;
    border-radius: 4px;
}

QMenuBar::item:selected {
    background-color: #3E4BB0;
    color: #FFFFFF;
}

QMenu {
    background-color: #1E2233;
    border: 1px solid #333A56;
    color: #E4E8F1;
    padding: 4px;
}

QMenu::item {
    padding: 5px 24px 5px 12px;
    border-radius: 4px;
}

QMenu::item:selected {
    background-color: #3E4BB0;
    color: #FFFFFF;
}

QMenu::separator {
    height: 1px;
    background: #333A56;
    margin: 4px 6px;
}

QMessageBox {
    background-color: #1E2233;
    color: #E4E8F1;
}

QMessageBox QLabel {
    color: #E4E8F1;
}
"""

THEMES = {
    "light": LIGHT_QSS,
    "dark": DARK_QSS,
}


def get_theme_qss(theme_name: str) -> str:
    return THEMES.get(theme_name, LIGHT_QSS)