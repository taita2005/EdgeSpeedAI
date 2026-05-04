import yaml
from src.utils.logger import logger
from src.core.analyzer import VideoAnalyzer
from src.utils.network_client import NetworkClient
from src.pipeline.violation_manager import ViolationManager
from src.pipeline.stream_handler import StreamHandler

def main():
    logger.info("="*50)
    logger.info("🚀 KHỞI ĐỘNG HỆ THỐNG EDGE SPEED AI")
    logger.info("="*50)

    # 1. Đọc cấu hình tổng
    config_path = "configs/app_config.yaml"
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    # 2. Khởi tạo các module (Mô hình Dependency Injection)
    logger.info("⚙️ Đang khởi tạo các module...")
    
    # Client gửi dữ liệu
    network_client = NetworkClient(backend_url=config['network']['backend_url'])
    
    # Module AI (YOLO + SpeedEstimator)
    analyzer = VideoAnalyzer(config_path)
    
    # Não bộ xử lý nghiệp vụ vi phạm
    violation_manager = ViolationManager(config, network_client)
    
    # Luồng Camera
    stream_handler = StreamHandler(
        analyzer=analyzer, 
        violation_manager=violation_manager, 
        debug_mode=config['system']['debug_mode']
    )

    # 3. Bắt đầu chạy hệ thống
    # Có thể đổi thành "0" cho webcam, hoặc "rtsp://..." cho camera IP
    video_source = "../data/13294696_1080_1920_30fps.mp4" 
    stream_handler.run(source=video_source)

if __name__ == "__main__":
    main()
