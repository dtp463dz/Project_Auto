# TPLabel (Auto Labeling Tool)

**TPLabel** là một ứng dụng máy tính (Desktop Application) mạnh mẽ được xây dựng bằng cấu trúc Python và giao diện hiện đại PyQt5. Công cụ này được thiết kế chuyên dụng cho việc quản lý, dán nhãn thủ công và tích hợp mô hình học sâu (như Ultralytics YOLO / Torch) để hỗ trợ **tự động dán nhãn dữ liệu hình ảnh (Auto-Labeling)** phục vụ cho các bài toán Computer Vision trong công nghiệp và nghiên cứu.

# TPLabel 
# Code by Happy22
---

## 📌 Tính năng chính

### 1. Quản lý dự án & File dữ liệu linh hoạt
* **Hỗ trợ đa định dạng:** Dễ dàng mở thư mục hình ảnh (`Open Dir`) và thư mục lưu trữ nhãn (`Change Save Dir`).
* **Định dạng nhãn chuẩn:** Quản lý danh sách lớp (classes) thông qua file `predefined_classes.txt` và lưu vết tọa độ nhãn theo định dạng YOLO (.txt).
* **Danh sách điều hướng trực quan:** Tích hợp File List và Label List giúp kiểm tra nhanh trạng thái dán nhãn của từng ảnh trong thư mục.

### 2. Canvas tương tác cao (Image Canvas)
* **Thao tác mượt mà:** Hỗ trợ phóng to, thu nhỏ (Zoom In/Out), kéo pan ảnh (Move Canvas) và đưa ảnh về trung tâm (Center Image).
* **Vẽ Box linh hoạt:** Tạo bounding box (`Create Box`), chỉnh sửa tọa độ kéo thả, thay đổi nhãn lớp, xóa box hoặc thực hiện các lệnh Hoàn tác/Làm lại (`Undo`/`Redo`) lên đến 100 bước lịch sử.

### 3. Cơ chế Tự động dán nhãn (Auto-Labeling)
* **Tích hợp Model AI:** Tích hợp mô hình học sâu (Ultralytics YOLO, PyTorch) để tự động phát hiện đối tượng trong tầm nhìn.
* **Luồng xử lý bất đồng bộ (Multi-threading):** Sử dụng `QThread` và `QWorker` để chạy tiến trình AI dán nhãn hàng loạt dưới nền (Background Process), giúp giao diện không bị đóng băng (Freeze) khi xử lý tập dữ liệu lớn.
* **Hộp thoại tiến độ:** Hiển thị `LoadingDialog` với Progress Bar cập nhật thời gian thực, cho phép người dùng theo dõi tiến độ tự động dán nhãn hoặc hủy tiến trình (`Cancel`) bất kỳ lúc nào.

### 4. Giao diện chuyên nghiệp & Phím tắt thuận tiện
* **Hệ thống Theme tối tối giản:** Giao diện được tối ưu màu sắc theo phong cách Dark Mode chuyên nghiệp, sử dụng thư viện `qtawesome` để đồng bộ hệ thống icon sắc nét.
* **Phím tắt chuẩn (Hotkeys):** Tích hợp các phím tắt tăng tốc độ dán nhãn (ví dụ: `A` để quay lại ảnh trước, `D` để sang ảnh tiếp theo, `W` để tạo vùng box mới...).

---

## 📁 Cấu trúc Thư mục Dự án

Dự án được tổ chức chặt chẽ theo kiến trúc mô-đun hóa:

```text
└── ./
    ├── TPLabel.py               # File thực thi và khởi tạo luồng ứng dụng chính (QApplication)
    ├── TPLabel.spec             # File cấu hình đóng gói PyInstaller (đã gom cụm torch/ultralytics)
    ├── tplabel.log              # File log ghi vết hoạt động và lỗi của hệ thống
    │
    ├── gui/                     # Quản lý giao diện và thẩm mỹ ứng dụng
    │   ├── main_window.py       # Cấu trúc giao diện chính, thanh Menu, Toolbar và bố cục DockWidgets
    │   ├── theme.py             # Định nghĩa stylesheet (QSS), bảng màu và phong cách giao diện
    │   └── logger.py            # Cấu hình ghi log hệ thống
    │
    ├── widgets/                 # Các Widget tùy biến nâng cao
    │   └── image_canvas.py      # Widget xử lý tương tác vẽ Bounding Box, Zoom, Pan và quản lý Undo/Redo
    │
    ├── logic/                   # Xử lý logic nghiệp vụ xử lý ngầm và AI
    │   ├── auto_label_logic.py  # Điều hướng logic gọi mô hình dán nhãn tự động
    │   └── auto_label_worker.py # Tiến trình chạy nền (QWorker) thực thi inference mô hình YOLO/Torch
    │
    ├── dialog/                  # Các hộp thoại tương tác phụ
    │   ├── dialog_lib.py        # Thư viện tiện ích tạo nhanh thông báo
    │   ├── loading_dialog.py    # Hộp thoại hiển thị thanh tiến trình khi chạy Auto-Label
    │   ├── new_label_dialog.py  # Hộp thoại tạo tên nhãn mới
    │   └── select_label_dialog.py # Hộp thoại lựa chọn nhanh nhãn từ danh sách lớp có sẵn
    │
    └── libs/                    # Các module chức năng bổ trợ (Actions & Shortcuts)
        ├── file_lib.py          # Logic liên quan đến Đọc/Ghi file ảnh và file nhãn
        ├── edit_lib.py          # Logic công cụ chỉnh sửa, tạo box, xóa box
        ├── view_lib.py          # Logic điều khiển thu phóng, căn chỉnh khung nhìn ảnh
        ├── help_lib.py          # Chức năng hiển thị thông tin hướng dẫn, phím tắt
        └── testQtawesome.py     # Script kiểm tra tài nguyên icon ứng dụng
