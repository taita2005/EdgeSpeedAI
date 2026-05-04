import os

# Lấy đường dẫn gốc của backend_app
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Cấu trúc thư mục lưu trữ
STORAGE_DIR = os.path.join(BASE_DIR, "storage")
IMAGES_DIR = os.path.join(STORAGE_DIR, "images")
CROPS_DIR = os.path.join(STORAGE_DIR, "crops")

# Chuỗi kết nối SQLite (Tạo file speedai.db ngay tại thư mục backend_app)
DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'speedai.db')}"

# Đảm bảo các thư mục tồn tại ngay khi khởi động
os.makedirs(IMAGES_DIR, exist_ok=True)
os.makedirs(CROPS_DIR, exist_ok=True)
