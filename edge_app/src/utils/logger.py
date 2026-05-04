import logging
import sys

def get_logger(name="EdgeSpeedAI"):
    """Khởi tạo logger chuẩn mực cho hệ thống."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        # Định dạng log: [Thời gian] - [Mức độ] - [Module] - Nội dung
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Log ra màn hình console
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
    return logger

logger = get_logger()
