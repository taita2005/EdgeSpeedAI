import json
from sqlalchemy.orm import Session
from app.db.models import ViolationRecord
from app.services.ocr_service import ocr_engine

def process_violation_task(violation_id: int, db: Session):
    """
    Hàm này sẽ chạy ngầm (Background Task). 
    Nhiệm vụ: Lọc DB, lấy ảnh, cắt ảnh, gọi OCR, cập nhật DB.
    """
    try:
        # Lấy record đang Pending
        record = db.query(ViolationRecord).filter(ViolationRecord.id == violation_id).first()
        if not record:
            return

        print(f"🔄 [Worker] Đang xử lý OCR cho Vi phạm ID: {violation_id}")
        
        # Parse BBox từ string sang list
        bbox = json.loads(record.bounding_box)
        
        # Chạy thuật toán OCR
        plate_text, crop_path = ocr_engine.process_and_read_plate(record.image_path, bbox)
        
        # Cập nhật Database
        record.crop_path = crop_path
        if plate_text:
            record.license_plate = plate_text
            record.status = "Completed"
            print(f"✅ [Worker] Xong ID {violation_id} -> Biển số: {plate_text}")
        else:
            record.status = "Failed"
            record.license_plate = "KHÔNG_NHẬN_DIỆN_ĐƯỢC"
            print(f"⚠️ [Worker] Xong ID {violation_id} -> Không đọc được biển số.")
            
        db.commit()

    except Exception as e:
        print(f"❌ [Worker] Lỗi nghiêm trọng: {e}")
        db.rollback()
