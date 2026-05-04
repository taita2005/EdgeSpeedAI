from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.core.config import DATABASE_URL

# Khởi tạo Engine SQLite
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Dependency để mở và đóng kết nối DB cho mỗi Request
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
