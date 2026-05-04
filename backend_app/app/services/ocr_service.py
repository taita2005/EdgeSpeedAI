import cv2
import os
import uuid
from paddleocr import PaddleOCR
from app.core.config import CROPS_DIR

class OCRService:
    def __init__(self):
        # Khởi tạo PaddleOCR (Chỉ load 1 lần vào RAM/VRAM khi khởi động)
        # lang='en' là đủ để nhận diện biển số VN (chữ cái latin + số)
        print("⏳ Đang khởi tạo mô hình PaddleOCR...")
        self.ocr = PaddleOCR(use_angle_cls=False, lang='en', enable_mkldnn=False)
        print("✅ PaddleOCR đã sẵn sàng!")

    def process_and_read_plate(self, image_path: str, bbox: list):
        """Cắt ảnh theo BBox và chạy OCR (Có cơ chế tự vệ chống lỗi ảnh rỗng)"""
        try:
            # 1. Đọc ảnh gốc bằng OpenCV
            img = cv2.imread(image_path)
            if img is None:
                raise ValueError("Không thể đọc file ảnh gốc")

            # Lấy kích thước ảnh thật để chặn không cho crop lố ra ngoài
            img_h, img_w = img.shape[:2]

            # 2. Xử lý tọa độ an toàn tuyệt đối
            x1, y1, x2, y2 = [int(v) for v in bbox]
            
            # Chặn tọa độ âm
            x1, y1 = max(0, x1), max(0, y1)
            # Chặn tọa độ tràn viền
            x2, y2 = min(img_w, x2), min(img_h, y2)

            # 3. KIỂM TRA BBOX RỖNG (TRỌNG TÂM SỬA LỖI Ở ĐÂY)
            if x1 >= x2 or y1 >= y2:
                print(f"⚠️ Bỏ qua crop: Tọa độ BBox không hợp lệ hoặc quá nhỏ: {bbox}")
                return None, None

            # 4. Tiến hành cắt (Crop)
            crop_img = img[y1:y2, x1:x2]

            # Kiểm tra chốt chặn cuối: Nếu ảnh vẫn rỗng thì hủy
            if crop_img.size == 0:
                print("⚠️ Bỏ qua crop: Ảnh cắt ra bị rỗng (Empty Image).")
                return None, None

            # 5. Lưu ảnh Crop
            crop_filename = f"crop_{uuid.uuid4().hex[:8]}.jpg"
            crop_path = os.path.join(CROPS_DIR, crop_filename)
            cv2.imwrite(crop_path, crop_img)

            # 6. Chạy PaddleOCR trên ảnh Crop
            results = self.ocr.ocr(crop_path)
            
            # 7. Phân tích kết quả text
            extracted_text = ""
            if results and results[0]:
                texts = [line[1][0] for line in results[0]]
                extracted_text = "-".join(texts) 
            
            return extracted_text.strip(), crop_path

        except Exception as e:
            print(f"❌ Lỗi OCR: {e}")
            return None, None

    # def process_and_read_plate(self, image_path: str, bbox: list):
    #     """Cắt ảnh theo BBox và chạy OCR"""
    #     try:
    #         # 1. Đọc ảnh gốc bằng OpenCV
    #         img = cv2.imread(image_path)
    #         if img is None:
    #             raise ValueError("Không thể đọc file ảnh gốc")

    #         # 2. Cắt ảnh (Crop) theo BBox [x1, y1, x2, y2]
    #         # Lưu ý an toàn: Đảm bảo tọa độ không vượt quá kích thước ảnh
    #         x1, y1, x2, y2 = [int(v) for v in bbox]
    #         x1, y1 = max(0, x1), max(0, y1)
    #         crop_img = img[y1:y2, x1:x2]

    #         # 3. Lưu ảnh Crop
    #         crop_filename = f"crop_{uuid.uuid4().hex[:8]}.jpg"
    #         crop_path = os.path.join(CROPS_DIR, crop_filename)
    #         cv2.imwrite(crop_path, crop_img)

    #         # 4. Chạy PaddleOCR trên ảnh Crop
    #         results = self.ocr.ocr(crop_path, cls=False)
            
    #         # 5. Phân tích kết quả text
    #         extracted_text = ""
    #         if results and results[0]:
    #             # results[0] là list các đoạn text tìm được: [[[tọa độ], ('text', độ_tin_cậy)], ...]
    #             texts = [line[1][0] for line in results[0]]
    #             extracted_text = "-".join(texts) # Ghép các dòng lại (nếu biển số 2 dòng)
            
    #         return extracted_text.strip(), crop_path

    #     except Exception as e:
    #         print(f"❌ Lỗi OCR: {e}")
    #         return None, None

# Khởi tạo biến toàn cục để dùng chung
ocr_engine = OCRService()
