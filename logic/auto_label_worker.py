from PyQt5.QtCore import QThread, pyqtSignal

class AutoLabelWorker(QThread):
    finished_signal = pyqtSignal(int)
    error_signal = pyqtSignal(str)

    def __init__(self, logic, image_dir, model_path, label_dir, conf=0.4):
        super().__init__()
        self.logic = logic
        self.image_dir = image_dir
        self.model_path = model_path
        self.label_dir = label_dir
        self.conf = conf
    
    def run(self):
        try:
            total = self.logic.run(
                image_dir = self.image_dir,
                model_path = self.model_path,
                label_dir = self.label_dir,
                conf = self.conf
            )
            self.finished_signal.emit(total)
        except Exception as e:
            self.error_signal.emit(str(e))
        