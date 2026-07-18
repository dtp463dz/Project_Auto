from PyQt5.QtCore import QThread, pyqtSignal
import threading

class AutoLabelWorker(QThread):
    finished_signal = pyqtSignal(int)
    error_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int, int, str)   # done, total, filename

    def __init__(self, logic, image_dir, model_path, label_dir, conf=0.4):
        super().__init__()
        self.logic = logic
        self.image_dir = image_dir
        self.model_path = model_path
        self.label_dir = label_dir
        self.conf = conf
        self._stop_event = threading.Event()
    def request_stop(self):
        self._stop_event.set()

    def _on_progress(self, done, total, filename):
        self.progress_signal.emit(done, total, filename)

    def run(self):
        try:
            total = self.logic.run(
                image_dir = self.image_dir,
                model_path = self.model_path,
                label_dir = self.label_dir,
                conf = self.conf,
                progress_callback = self._on_progress,
                should_stop = self._stop_event.is_set
            )
            self.finished_signal.emit(total)
        except Exception as e:
            self.error_signal.emit(str(e))
        