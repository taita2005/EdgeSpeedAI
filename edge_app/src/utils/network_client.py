import requests
import json
from src.utils.logger import logger

class NetworkClient:
    def __init__(self, backend_url, timeout=5):
        self.backend_url = backend_url
        self.timeout = timeout

    def send_violation(self, image_path, metadata_path):
        """
        Đóng gói ảnh và metadata để gửi POST request sang Backend.
        Backend sẽ đưa request này vào Queue để xử lý OCR.
        """
        try:
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)

            # Đọc file ảnh dưới dạng nhị phân
            with open(image_path, 'rb') as f:
                files = {'image': (image_path.split('/')[-1], f, 'image/jpeg')}
                data = {'metadata': json.dumps(metadata)}
                
                # logger.info(f"🚀 Đang gửi dữ liệu vi phạm của ID {metadata['track_id']} sang Backend...")
                
                # Gửi request (Edge không cần chờ OCR, Backend chỉ trả về 200 OK ngay lập tức)
                response = requests.post(self.backend_url, files=files, data=data, timeout=self.timeout)
                
            if response.status_code == 200:
                # logger.info(f"✅ Gửi thành công! Backend đã cho vào hàng đợi (Queue).")
                return True
            else:
                # logger.error(f"❌ Backend trả về lỗi: {response.status_code} - {response.text}")
                return False

        except requests.exceptions.RequestException as e:
            logger.error(f"🌐 Lỗi kết nối mạng: Backend không phản hồi. ({e})")
            return False
        except Exception as e:
            logger.error(f"⚠️ Lỗi không xác định khi gửi data: {e}")
            return False
