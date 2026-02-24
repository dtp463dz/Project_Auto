from PyQt5.QtCore import QThread, pyqtSignal

class AutoLabelWorker(QThread):
    finished_signal = pyqtSignal(int)
    error_signal = pyqtSignal(str)

    def __init__(self, logic, image_dir, model_path, label_dir):
        super().__init__()
        self.logic = logic
        self.image_dir = image_dir
        self.model_path = model_path
        self.label_dir = label_dir
    
    def run(self):
        try:
            total = self.logic.run(
                image_dir = self.image_dir,
                model_path = self.model_path,
                label_dir = self.label_dir
            )
            self.finished_signal.emit(total)
        except Exception as e:
            self.error_signal.emit(str(e))
        