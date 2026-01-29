# chọn folder, confirm
from PyQt5.QtWidgets import QFileDialog, QMessageBox


class DialogLib:

    @staticmethod
    def select_image_folder(parent):
        return QFileDialog.getExistingDirectory(
            parent, "Select Image Folder"
        )

    @staticmethod
    def select_model_file(parent):
        return QFileDialog.getOpenFileName(
            parent,
            "Select YOLO Model",
            "",
            "YOLO Model (*.pt)"
        )[0]

    @staticmethod
    def select_label_folder(parent):
        return QFileDialog.getExistingDirectory(
            parent, "Select Label Folder"
        )

    @staticmethod
    def confirm(parent, image_count, model_path, label_dir):
        msg = (
            f"Bạn có chắc muốn auto label?\n\n"
            f"📂 Ảnh: {image_count}\n"
            f"🤖 Model: {model_path}\n"
            f"📁 Output: {label_dir}"
        )

        return QMessageBox.question(
            parent,
            "Confirm Auto Label",
            msg,
            QMessageBox.Yes | QMessageBox.No
        ) == QMessageBox.Yes
