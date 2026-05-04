import yaml
from ultralytics import solutions
from src.utils.logger import logger

class VideoAnalyzer:
    def __init__(self, config_path="configs/app_config.yaml"):
        # Đọc cấu hình
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
            
        model_cfg = self.config['model']
        speed_cfg = self.config['speed']

        logger.info(f"Khởi tạo SpeedEstimator với model: {model_cfg['path']}")
        
        # Khởi tạo module có sẵn của Ultralytics
        self.speed_estimator = solutions.SpeedEstimator(
            model=model_cfg['path'],
            fps=speed_cfg['fps'],
            meter_per_pixel=speed_cfg['meter_per_pixel'],
            max_hist=speed_cfg['max_hist'],
            max_speed=speed_cfg['max_speed'],
            classes=model_cfg['classes'],
            show=False  # Tắt show mặc định, chúng ta tự quản lý việc hiển thị
        )

    def process_frame(self, frame):
        """
        Đưa frame vào SpeedEstimator.
        Trả về frame đã vẽ và danh sách dữ liệu để Violation Manager xử lý.
        """
        # Gọi hàm xử lý cốt lõi của Ultralytics
        output = self.speed_estimator(frame)
        
        # Xử lý tương thích
        if hasattr(output, 'plot_im'):
            annotated_frame = output.plot_im
        elif isinstance(output, list) and hasattr(output[0], 'plot_im'):
            annotated_frame = output[0].plot_im
        else:
            annotated_frame = output
        
        tracking_data = []
        
        # --- ĐOẠN HOOK (MÓC DỮ LIỆU) HOÀN THIỆN ---
        try:
            # 1. Tìm dictionary chứa tốc độ
            speed_dict = getattr(self.speed_estimator, 'spd', 
                         getattr(self.speed_estimator, 'speed', 
                         getattr(self.speed_estimator, 'speeds', {})))
            
            # 2. Tìm danh sách ID và Boxes gốc
            t_ids = getattr(self.speed_estimator, 'trk_ids', getattr(self.speed_estimator, 'track_ids', []))
            b_boxes = getattr(self.speed_estimator, 'boxes', getattr(self.speed_estimator, 'trk_boxes', []))
            
            # 3. CHUẨN HÓA DỮ LIỆU
            id_to_bbox = {}
            
            if hasattr(t_ids, 'tolist'):
                t_ids = t_ids.tolist()
            elif hasattr(t_ids, 'cpu'):
                t_ids = t_ids.cpu().numpy().tolist()
                
            if hasattr(b_boxes, 'xyxy'): 
                b_boxes = b_boxes.xyxy.cpu().numpy().tolist()
            elif hasattr(b_boxes, 'tolist'): 
                b_boxes = b_boxes.tolist()
            elif hasattr(b_boxes, 'cpu'):
                b_boxes = b_boxes.cpu().numpy().tolist()

            # 4. Ghép ID với BBox
            if isinstance(t_ids, list) and isinstance(b_boxes, list) and len(t_ids) == len(b_boxes):
                for i in range(len(t_ids)):
                    veh_id = int(t_ids[i]) 
                    id_to_bbox[veh_id] = [int(v) for v in b_boxes[i]]

            # 5. ĐÓNG GÓI (LOGIC MỚI LỌC BỎ [0,0,0,0])
            for track_id, speed in speed_dict.items():
                t_id_int = int(track_id)
                
                # CHỈ lấy những xe VỪA có tốc độ, VỪA có BBox hiện diện ở khung hình này
                if speed > 0 and t_id_int in id_to_bbox:
                    tracking_data.append({
                        "id": t_id_int,
                        "speed": speed,
                        "bbox": id_to_bbox[t_id_int]
                    })
                    
        except Exception as e:
            logger.error(f"🚨 LỖI TRÍCH XUẤT DỮ LIỆU TỪ ULTRALYTICS: {e}")
            
        return annotated_frame, tracking_data