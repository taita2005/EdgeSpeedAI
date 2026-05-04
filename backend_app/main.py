from fastapi import FastAPI
from app.api import endpoints
from app.db.database import engine, Base

# Lệnh này sẽ tự động tạo bảng trong SQLite nếu chưa có
Base.metadata.create_all(bind=engine)

app = FastAPI(title="EdgeSpeedAI Backend", version="1.0.0")

# Nhúng các API router vào app chính
app.include_router(endpoints.router, prefix="/api/v1", tags=["Violations"])

@app.get("/")
def root():
    return {"message": "Hệ thống Backend EdgeSpeedAI đang hoạt động 🚀"}

# CÁCH CHẠY CODE NÀY:
# Mở terminal tại thư mục backend_app/ và gõ:
# uvicorn main:app --host 0.0.0.0 --port 8000 --reload
