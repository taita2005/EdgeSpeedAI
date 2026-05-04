from sqlalchemy import Column, Integer, String, Float, DateTime
from app.db.database import Base
import datetime

class ViolationRecord(Base):
    __tablename__ = "violations"

    id = Column(Integer, primary_key=True, index=True)
    edge_id = Column(String, index=True)
    track_id = Column(Integer)
    timestamp = Column(String)       # Lưu chuỗi thời gian Edge gửi lên
    
    speed_kmh = Column(Float)
    speed_limit = Column(Float)
    
    image_path = Column(String)      # Đường dẫn ảnh gốc lưu trên Server
    crop_path = Column(String)       # Đường dẫn ảnh crop biển số
    
    bounding_box = Column(String)    # Lưu list [x1, y1, x2, y2] dưới dạng string
    license_plate = Column(String, nullable=True) # Biển số text (PaddleOCR giải mã)
    
    # Trạng thái: Pending (Đang đợi OCR), Completed (Đã xong), Failed (Lỗi OCR)
    status = Column(String, default="Pending") 
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
