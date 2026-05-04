import os
import cv2
import json
from datetime import datetime
from src.utils.logger import logger

class ViolationManager:
    def __init__(self, config, network_client):
        self.config = config
        self.limit_kmh = config['speed']['limit_kmh']
        self.edge_id = config['system']['edge_id']
        self.network_client = network_client
        
        # Dictionary lưu xe ĐANG vi phạm trong màn hình
        # {id: {'best_frame': img, 'bbox': [], 'max_speed': float, 'max_area': float, 'timestamp': str}}
        self.active_violators = {}
        
        # Đảm bảo thư mục lưu trữ cục bộ tồn tại
        os.makedirs("results/snapshots", exist_ok=True)
        os.makedirs("results/metadata", exist_ok=True)

    def update(self, tracking_data, annotated_frame):
        """Cập nhật trạng thái xe. Chọn ảnh BBox lớn nhất và chốt gửi khi xe qua tâm."""
        current_ids = set()
        
        # Lấy chiều cao của video để tính đường tâm (center line)
        frame_height, frame_width = annotated_frame.shape[:2]
        center_y_frame = frame_height / 2

        # 1. LỌC VÀ CẬP NHẬT XE VI PHẠM
        for data in tracking_data:
            veh_id = data['id']
            speed = data['speed']
            bbox = data.get('bbox', [0, 0, 0, 0])
            
            # Tính diện tích và tọa độ tâm y (cy) của BBox
            x1, y1, x2, y2 = bbox
            area = (x2 - x1) * (y2 - y1)
            
            current_ids.add(veh_id)

            # NẾU PHÁT HIỆN VI PHẠM TỐC ĐỘ
            if speed > self.limit_kmh:
                if veh_id not in self.active_violators:
                    logger.warning(f"🚨 Phát hiện ID {veh_id} vi phạm tốc độ: {speed:.1f} km/h")
                    self.active_violators[veh_id] = {
                        "max_speed": speed,
                        "best_frame": annotated_frame.copy(),
                        "bbox": bbox,
                        "max_area": area,  # Dùng diện tích BBox làm thước đo độ nét
                        "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S")
                    }
                else:
                    # LOGIC MỚI: Cập nhật "Best Frame" nếu BBox to hơn (gần camera hơn)
                    if area > self.active_violators[veh_id]['max_area']:
                        # Luôn giữ lại con số tốc độ vi phạm cao nhất để báo cáo
                        self.active_violators[veh_id]['max_speed'] = max(speed, self.active_violators[veh_id]['max_speed'])
                        self.active_violators[veh_id]['max_area'] = area
                        self.active_violators[veh_id]['best_frame'] = annotated_frame.copy()
                        self.active_violators[veh_id]['bbox'] = bbox

        # 2. XÁC ĐỊNH XE ĐÃ RỜI KHỎI VÙNG QUAN SÁT (LOST IDs)
        # Cách 1: Xe bị mất track hoàn toàn (đi khuất)
        lost_ids = list(self.active_violators.keys() - current_ids)
        
        # Cách 2: LOGIC MỚI - Tâm xe vượt qua tâm màn hình
        for veh_id in list(self.active_violators.keys()):
            if veh_id in current_ids:  # Xe vẫn đang được track
                # Tìm lại data của xe này trong frame hiện tại
                for data in tracking_data:
                    if data['id'] == veh_id:
                        x1, y1, x2, y2 = data.get('bbox', [0, 0, 0, 0])
                        cy = (y1 + y2) / 2  # Tính lại tâm Y hiện tại
                        
                        # Giả định xe đi từ đáy màn hình (gần) chạy lên phía trên (xa dần)
                        # Khi cy < center_y_frame tức là xe đã vượt qua nửa trên màn hình -> Chốt hạ
                        # (Nếu video của bạn xe chạy từ trên xuống dưới, hãy đổi dấu < thành > nhé)
                        if cy < center_y_frame:
                            if veh_id not in lost_ids:
                                lost_ids.append(veh_id)
                        break

        # 3. CHỐT HẠ VÀ GỬI API
        if len(lost_ids) > 0:
            logger.info(f"⚠️ Các xe vi phạm sau đã vượt qua tâm/rời hình: {lost_ids}")
            
        for veh_id in lost_ids:
            # Kiểm tra tránh pop 2 lần do logic trùng lặp
            if veh_id in self.active_violators: 
                self._finalize_violation(veh_id)

    def _finalize_violation(self, veh_id):
        """Xử lý đóng gói và gửi dữ liệu khi xe vi phạm đã đi khuất."""
        record = self.active_violators.pop(veh_id)
        
        timestamp = record['timestamp']
        speed = int(record['max_speed'])
        
        # Format tên file: YYYYMMDD_HHMMSS_ID[xxx]_SPEED[yyy].jpg
        file_prefix = f"{timestamp}_ID{veh_id:03d}_SPEED{speed}"
        img_path = f"results/snapshots/{file_prefix}.jpg"
        meta_path = f"results/metadata/{file_prefix}.json"

        # 1. Lưu ảnh (Đã vẽ BBox và text)
        cv2.imwrite(img_path, record['best_frame'])
        
        # 2. Tạo file JSON metadata (Cho Backend biết cần crop chỗ nào để OCR)
        metadata = {
            "edge_id": self.edge_id,
            "track_id": veh_id,
            "timestamp": timestamp,
            "speed_kmh": record['max_speed'],
            "speed_limit": self.limit_kmh,
            "bounding_box": record['bbox']  # Gửi tọa độ BBox to nhất lúc ở đáy màn hình
        }
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=4)
            
        logger.info(f"📸 Đã lưu Best Frame cực nét cục bộ: {img_path}")

        # 3. Kích hoạt Network Client gửi sang Backend
        self.network_client.send_violation(img_path, meta_path)

    def flush_all(self):
        """Chốt hạ toàn bộ xe vi phạm còn kẹt lại trên màn hình khi kết thúc video."""
        remaining_ids = list(self.active_violators.keys())
        if remaining_ids:
            logger.info(f"🧹 Đang chốt hạ và gửi nốt {len(remaining_ids)} xe vi phạm còn sót lại trước khi tắt máy...")
            for veh_id in remaining_ids:
                self._finalize_violation(veh_id)