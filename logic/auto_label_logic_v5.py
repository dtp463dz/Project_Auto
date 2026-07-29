"""
auto_label_logic_v5.py - Auto-label dành riêng cho model YOLOv5 GỐC
(train bằng repo https://github.com/ultralytics/yolov5).

LÝ DO CẦN FILE RIÊNG:
Theo tài liệu chính thức Ultralytics: "Models trained with the
ultralytics/yolov5 repo cannot be loaded with the ultralytics/ultralytics
library." Tức là `from ultralytics import YOLO; YOLO(model_path)` (đang dùng
trong auto_label_logic.py cho v8/v9/v10/v11) sẽ KHÔNG load được checkpoint
v5 gốc (kiến trúc pickle khác nhau) - phải dùng package `yolov5` riêng
(pip install yolov5) mới load đúng.

Có cùng chữ ký run(...) như AutoLabelLogic (v8/v11) nên AutoLabelWorker
dùng chung được, không cần sửa gì ở worker.
"""

import os
import pathlib
from PIL import Image


class AutoLabelLogicV5:
    def __init__(self):
        self.model = None
        self.model_path = None

    def load_model(self, model_path):
        if not model_path:
            raise ValueError("Model path is not set.")
        if self.model is not None and self.model_path == model_path:
            return   # đã load đúng model này rồi, không load lại

        import yolov5   # import trễ - chỉ những ai thực sự dùng nút v5 mới cần cài package này

        # bảo vệ tương tự auto_label_logic.py (checkpoint train trên Windows,
        # chạy trên Linux có thể lỗi path) - nhưng CHỈ bọc quanh đúng lệnh load,
        # không để ảnh hưởng toàn app
        original_posix_path = pathlib.PosixPath
        try:
            pathlib.PosixPath = pathlib.WindowsPath
            self.model = yolov5.load(model_path)
        finally:
            pathlib.PosixPath = original_posix_path

        self.model_path = model_path

    def _names_list(self):
        names = self.model.names
        if isinstance(names, dict):
            return [names[i] for i in sorted(names.keys())]
        return list(names)

    def run(self, image_dir, model_path, label_dir, conf=0.4,
            progress_callback=None, should_stop=None):
        """
        progress_callback(done, total, filename) - gọi sau khi xử lý xong mỗi ảnh.
        should_stop() -> bool - nếu trả True, dừng sớm (ảnh đã xử lý vẫn giữ nguyên).
        """
        if not os.path.exists(label_dir):
            os.makedirs(label_dir)

        self.load_model(model_path)
        self.model.conf = conf   # package `yolov5` dùng thuộc tính .conf để set ngưỡng

        names_list = self._names_list()
        classes_path = os.path.join(label_dir, "classes.txt")
        if not os.path.exists(classes_path):
            with open(classes_path, "w", encoding="utf-8") as f:
                for name in names_list:
                    f.write(name + "\n")

        images = [
            f for f in os.listdir(image_dir)
            if f.lower().endswith((".jpg", ".png", ".jpeg"))
        ]

        total = len(images)
        done = 0
        for filename in images:
            if should_stop is not None and should_stop():
                break

            image_path = os.path.join(image_dir, filename)
            results = self.model(image_path)

            with Image.open(image_path) as img:
                w, h = img.size

            label_path = os.path.join(
                label_dir,
                os.path.splitext(filename)[0] + ".txt"
            )
            # results.pred[0]: tensor [N, 6] = x1, y1, x2, y2, conf, cls
            preds = results.pred[0]
            with open(label_path, "w") as f:
                for *xyxy, score, cls_id in preds.tolist():
                    x1, y1, x2, y2 = xyxy
                    cx = (x1 + x2) / 2 / w
                    cy = (y1 + y2) / 2 / h
                    bw = (x2 - x1) / w
                    bh = (y2 - y1) / h
                    f.write(
                        f"{int(cls_id)} "
                        f"{cx:.6f} {cy:.6f} "
                        f"{bw:.6f} {bh:.6f}\n"
                    )
            done += 1
            if progress_callback is not None:
                progress_callback(done, total, filename)
        return done
