import os
import json
from fastapi import APIRouter, UploadFile, File, Form, BackgroundTasks, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import ViolationRecord
from app.core.config import IMAGES_DIR
from app.services.queue_worker import process_violation_task

router = APIRouter()

@router.post("/upload-violation")
async def upload_violation(
    background_tasks: BackgroundTasks, # Hàng đợi của FastAPI
    image: UploadFile = File(...),     # Nhận file ảnh
    metadata: str = Form(...),         # Nhận JSON text
    db: Session = Depends(get_db)
):
    # 1. Lưu file ảnh gốc vào thư mục storage/images/
    image_path = os.path.join(IMAGES_DIR, image.filename)
    with open(image_path, "wb") as buffer:
        buffer.write(await image.read())

    # 2. Phân tích chuỗi JSON metadata từ Edge gửi lên
    data = json.loads(metadata)

    # 3. Lưu thông tin vào Database (Trạng thái Pending)
    new_violation = ViolationRecord(
        edge_id=data.get("edge_id"),
        track_id=data.get("track_id"),
        timestamp=data.get("timestamp"),
        speed_kmh=data.get("speed_kmh"),
        speed_limit=data.get("speed_limit"),
        image_path=image_path,
        bounding_box=json.dumps(data.get("bounding_box", [0,0,0,0])),
        status="Pending"
    )
    db.add(new_violation)
    db.commit()
    db.refresh(new_violation) # Lấy ID vừa tạo

    # 4. Đẩy Task phân tích OCR vào HÀNG ĐỢI NGẦM (Background)
    # Lệnh này không chờ OCR chạy xong, API sẽ lập tức chạy xuống lệnh return.
    background_tasks.add_task(process_violation_task, new_violation.id, db)

    # 5. Trả lời Edge ngay lập tức
    return {
        "status": "success", 
        "message": "Đã tiếp nhận vi phạm, đang xếp hàng chờ OCR.",
        "violation_id": new_violation.id
    }
