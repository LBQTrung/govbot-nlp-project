from scraper.agency_scraper import AgencyScraper
import threading
from concurrent.futures import ThreadPoolExecutor
import logging
from datetime import datetime
import os
from dotenv import load_dotenv

# Load biến môi trường từ file .env
load_dotenv()

def setup_logger():
    """Thiết lập logger cho quá trình crawl chung"""
    # Tạo thư mục logs nếu chưa tồn tại
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # Tạo logger cho crawl_list
    logger = logging.getLogger('crawl_list')
    logger.setLevel(logging.INFO)
    
    # Xóa handlers cũ nếu có
    if logger.handlers:
        logger.handlers.clear()
    
    # Tạo file handler cho log chung
    log_filename = f"logs/crawl_list_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    file_handler = logging.FileHandler(log_filename, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    
    # Tạo console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # Định dạng log
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Thêm handlers vào logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

def scrape_agency(agency_name: str, mongo_config: dict, logger):
    """Hàm crawl dữ liệu cho một agency"""
    scraper = AgencyScraper(agency_name, mongo_config, logger)
    scraper.scrape()

def main():
    # Danh sách các agency cần crawl
    agencies = [
        'Bộ Công an', 'Bộ Công thương', 'Bộ Dân tộc và Tôn giáo', 
        'Bộ Giáo dục và Đào tạo', 'Bộ Khoa học và Công nghệ', 
        'Bộ Ngoại giao', 'Bộ Nội vụ', 'Bộ Nông nghiệp và Môi trường', 
        'Bộ Quốc phòng', 'Bộ Tài chính', 'Bộ Tư pháp', 
        'Bộ Văn hóa, Thể thao và Du lịch', 'Bộ Xây dựng', 'Bộ Y tế', 
        'Bảo hiểm xã hội Việt Nam', 'Ngân hàng Chính sách xã hội', 
        'Ngân hàng Nhà nước Việt Nam', 'Ngân hàng phát triển Việt Nam', 
        'Thanh tra Chính phủ', 'Tòa án nhân dân', 
        'Tập đoàn Điện lực Việt Nam', 'Văn phòng Chính phủ', 
        'Văn phòng Trung ương Đảng'
    ]

    # Lấy MongoDB URI từ biến môi trường
    mongo_uri = os.getenv('MONGODB_URI')
    if not mongo_uri:
        raise ValueError("MONGODB_URI không được tìm thấy trong biến môi trường")

    # Cấu hình MongoDB
    mongo_config = {
        'uri': mongo_uri,
        'db': 'govbot',
        'collection': 'procedures'
    }

    # Thiết lập logger
    logger = setup_logger()
    logger.info(f"Bắt đầu crawl dữ liệu cho {len(agencies)} agency")

    # Sử dụng ThreadPoolExecutor để chạy đồng thời
    max_workers = 10
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(scrape_agency, agency, mongo_config, logger)
            for agency in agencies
        ]
        
        # Đợi tất cả các task hoàn thành
        for future in futures:
            future.result()

    logger.info("Hoàn thành crawl dữ liệu cho tất cả các agency")

if __name__ == "__main__":
    main()

