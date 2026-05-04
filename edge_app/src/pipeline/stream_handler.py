import cv2
from src.utils.logger import logger

class StreamHandler:
    def __init__(self, analyzer, violation_manager, debug_mode=True):
        self.analyzer = analyzer
        self.violation_manager = violation_manager
        self.debug_mode = debug_mode

    def run(self, source="data/samples/test_video.mp4"):
        """Vòng lặp chính xử lý từng khung hình."""
        cap = cv2.VideoCapture(source)
        if not cap.isOpened():
            logger.error(f"❌ Không thể mở luồng video từ: {source}")
            return

        logger.info(f"▶️ Bắt đầu xử lý luồng: {source}")

        while cap.isOpened():
            success, frame = cap.read()
            if not success:
                logger.info("🎬 Đã kết thúc video hoặc mất tín hiệu luồng.")
                break

            # Bước 1: AI Nhận diện & Tính tốc độ
            annotated_frame, tracking_data = self.analyzer.process_frame(frame)

            # Bước 2: Logic bắt vi phạm & lưu Best Frame
            # print(tracking_data)
            # print(annotated_frame)
            self.violation_manager.update(tracking_data, annotated_frame)

            # Bước 3: Hiển thị debug (chỉ chạy trên Laptop, tắt trên Jetson cho nhẹ)
            if self.debug_mode:
                cv2.imshow("EdgeSpeedAI - Realtime Tracking", annotated_frame)
                # Bấm 'q' để thoát
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    logger.info("🛑 Đã nhận lệnh dừng từ người dùng.")
                    break

        # Dọn dẹp tài nguyên
        cap.release()
        
        # Chỉ gọi hàm đóng cửa sổ nếu đang chạy ở chế độ debug (có UI)
        if self.debug_mode:
            try:
                cv2.destroyAllWindows()
            except:
                pass
