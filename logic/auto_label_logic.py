from ultralytics import YOLO
from PIL import Image
import os
import pathlib


temp = pathlib.PosixPath
pathlib.PosixPath = pathlib.WindowsPath
class AutoLabelLogic:
    def __init__(self):
        self.model = None
        
    def load_model(self, model_path):
        if self.model is None:
            if not model_path:
                raise ValueError("Model path is not set.")
            self.model = YOLO(model_path)

    def run(self, image_dir, model_path, label_dir, conf = 0.7):
        if not os.path.exists(label_dir):
            os.makedirs(label_dir)

        self.load_model(model_path)
        images = [
            f for f in os.listdir(image_dir)
            if f.lower().endswith((".jpg", ".png", ".jpeg"))
        ]

        for filename in images:
            image_path = os.path.join(image_dir, filename)
            results = self.model(image_path, conf=conf)

            with Image.open(image_path) as img:
                w, h = img.size

            label_path = os.path.join(
                label_dir,
                os.path.splitext(filename)[0] + ".txt"
            )
            with open(label_path, "w") as f:
                    for r in results:
                        for box in r.boxes:
                            cls_id = int(box.cls[0])
                            x, y, bw, bh = box.xywh[0]

                            f.write(
                                f"{cls_id} "
                                f"{x/w:.6f} {y/h:.6f} "
                                f"{bw/w:.6f} {bh/h:.6f}\n"
                            )
        return len(images)


