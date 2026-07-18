# chọn folder, confirm
from PyQt5.QtWidgets import QFileDialog, QMessageBox
from dialog.auto_label_confirm_dialog import AutoLabelConfirmDialog

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

    # def confirm(parent, image_count, model_path, label_dir):
    #     msg = (
    #         f"Bạn có chắc muốn auto label?\n\n"
    #         f"📂 Ảnh: {image_count}\n"
    #         f"🤖 Model: {model_path}\n"
    #         f"📁 Output: {label_dir}"
    #     )

    #     return QMessageBox.question(
    #         parent,
    #         "Confirm Auto Label",
    #         msg,
    #         QMessageBox.Yes | QMessageBox.No
    #     ) == QMessageBox.Yes
    
    @staticmethod
    def confirm(parent, image_count, model_path, label_dir):
        """Hiện dialog xác nhận + cho chỉnh confidence threshold.
        Trả về tuple (ok: bool, conf: float | None)."""
        dialog = AutoLabelConfirmDialog(parent, image_count, model_path, label_dir)
        if dialog.exec_() == AutoLabelConfirmDialog.Accepted:
            return True, dialog.get_conf()
        return False, None
