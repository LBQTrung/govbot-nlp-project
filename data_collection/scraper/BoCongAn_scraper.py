import json
import time
import logging
from datetime import datetime
from typing import List, Dict, Optional
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from tqdm import tqdm
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

class BoCongAnScraper:
    def __init__(self, mongo_config: dict, logger: logging.Logger):
        self.base_url = "https://dichvucong.bocongan.gov.vn/bocongan/bothutuc/listThuTuc"
        self.selectors = {
            "current_page": "li.active a.page-link",
            "next_page": "li a.page-link"
        }
        self.logger = logger
        self.setup_driver()
        self.setup_mongodb(mongo_config)
        self.collected_data = []


    def log_info(self, message: str):
        """Ghi log thông tin"""
        self.logger.info(message)

    def log_error(self, message: str):
        """Ghi log lỗi"""
        self.logger.error(message)

    def setup_driver(self):
        """Setup Chrome WebDriver with appropriate options"""
        chrome_options = Options()
        # chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        try:
            service = Service("../chrome_driver/chromedriver.exe")
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.wait = WebDriverWait(self.driver, 20)
        except Exception as e:
            print(f"Error initializing Chrome WebDriver: {str(e)}")
            raise

    def wait_for_page_load(self):
        """Đợi cho đến khi trang load xong"""
        self.wait.until(
            lambda driver: driver.execute_script("return document.readyState") == "complete"
        )
        time.sleep(2)

    def click_element(self, selector: str):
        """Click on an element with waiting"""
        try:
            element = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
            self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
            time.sleep(1)
            element.click()
        except TimeoutException:
            print(f"Timeout waiting for element: {selector}")
            raise

    def get_current_page(self) -> int:
        """Lấy số trang hiện tại"""
        try:
            current_page_element = self.driver.find_element(By.CSS_SELECTOR, self.selectors["current_page"])
            return int(current_page_element.text)
        except (NoSuchElementException, ValueError):
            return 1

    def has_next_page(self) -> bool:
        """Kiểm tra xem có trang tiếp theo không"""
        try:
            page_elements = self.driver.find_elements(By.CSS_SELECTOR, self.selectors["next_page"])
            current_page = self.get_current_page()
            
            for elem in page_elements:
                try:
                    page_num = int(elem.text)
                    if page_num > current_page:
                        return True
                except ValueError:
                    continue
            return False
        except Exception:
            return False

    def go_to_next_page(self):
        """Chuyển đến trang tiếp theo"""
        try:
            page_elements = self.driver.find_elements(By.CSS_SELECTOR, self.selectors["next_page"])
            current_page = self.get_current_page()
            
            for elem in page_elements:
                try:
                    page_num = int(elem.text)
                    if page_num > current_page:
                        elem.click()
                        time.sleep(3)  # Đợi trang mới load
                        return True
                except ValueError:
                    continue
            return False
        except Exception as e:
            print(f"Error going to next page: {str(e)}")
            return False

    def setup_mongodb(self, mongo_config: dict):
        """Thiết lập kết nối MongoDB"""
        try:
            self.client = MongoClient(mongo_config['uri'])
            # Kiểm tra kết nối
            self.client.admin.command('ping')
            self.db = self.client[mongo_config['db']]
            self.collection = self.db[mongo_config['collection']]
            self.log_info("Kết nối MongoDB thành công")
        except ConnectionFailure as e:
            self.log_error(f"Không thể kết nối đến MongoDB: {str(e)}")
            raise

    def save_to_mongodb(self, procedures: List[Dict]):
        """Lưu danh sách thủ tục vào MongoDB"""
        try:
            if procedures:
                # Thêm thông tin agency và thời gian thu thập
                for procedure in procedures:
                    procedure['collected_at'] = datetime.now()
                
                # Lưu vào MongoDB
                result = self.collection.insert_many(procedures)
                self.log_info(f"Đã lưu {len(result.inserted_ids)} thủ tục vào MongoDB")
        except Exception as e:
            self.log_error(f"Lỗi khi lưu vào MongoDB: {str(e)}")
            raise

    def collect_page_data(self):
        """Thu thập dữ liệu từ trang hiện tại"""
        try:
            # Lấy tất cả các hàng trong bảng
            rows = self.driver.find_elements(By.CSS_SELECTOR, ".list-tthc li a.tthc-name")
            page_procedures = []
            
            for index, row in enumerate(rows):
                try:
                    service_info = {
                        "ten": row.text,
                        "url": row.get_attribute("href"),
                        "status": "pending"
                    }
                    page_procedures.append(service_info)
                    self.collected_data.append(service_info)
                except Exception as e:
                    current_page = self.get_current_page()
                    self.log_error(f"Lỗi khi thu thập dữ liệu hàng {index+1} - Trang: {current_page}")
                    continue
            
            # Lưu dữ liệu của trang hiện tại vào MongoDB
            if page_procedures:
                self.save_to_mongodb(page_procedures)
                    
        except Exception as e:
            current_page = self.get_current_page()
            self.log_error(f"Lỗi khi thu thập dữ liệu trang {current_page}: {str(e)}")


    def scrape(self):
        """Thực hiện quá trình thu thập dữ liệu"""
        try:
            self.driver.get(self.base_url)
            self.wait_for_page_load()

            # Chọn số hàng hiện thị tối đa
            self.click_element("#pageSize")
            time.sleep(1)

            # Chọn option có giá trị 50
            option = self.driver.find_element(By.CSS_SELECTOR, "#pageSize option[value='50']")
            option.click()
            time.sleep(2)  # Đợi trang load lại với số hàng mới
            

            self.log_info(f"Bắt đầu thu thập dữ liệu")
            
            # Thu thập dữ liệu từ tất cả các trang
            total_pages = 0
            while True:
                current_page = self.get_current_page()
                total_pages = max(total_pages, current_page)
                
                # Đếm số bản ghi trước khi thu thập
                records_before = len(self.collected_data)
                
                # Thu thập dữ liệu
                self.collect_page_data()
                
                # Đếm số bản ghi sau khi thu thập
                records_after = len(self.collected_data)
                records_collected = records_after - records_before
                print(f"Trang {current_page} - Số bản ghi thu thập được: {records_collected}")
                
                if not self.has_next_page():
                    break
                    
                if not self.go_to_next_page():
                    break
            
            self.log_info(f"Hoàn thành thu thập dữ liệu- Tổng số trang: {total_pages} - Tổng số bản ghi thu thập được: {len(self.collected_data)}")
            
        except Exception as e:
            self.log_error(f"Lỗi: {str(e)}")
        finally:
            self.driver.quit()
            # Đóng kết nối MongoDB
            if hasattr(self, 'client'):
                self.client.close()

    def save_to_json(self, filename: Optional[str] = None):
        """Lưu dữ liệu thu thập được vào file JSON"""
        if filename is None:
            filename = f"data/{self.agency_name.replace(' ', '_')}_data.json"
            
        # Tạo thư mục data nếu chưa tồn tại
        import os
        if not os.path.exists('data'):
            os.makedirs('data')
            
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.collected_data, f, ensure_ascii=False, indent=2)
        self.log_info(f"Đã lưu dữ liệu vào file {filename}")


if __name__ == "__main__":
    mongo_config = {
        "uri": "mongodb+srv://lebaquoctrung:lebaquoctrung@botgovcluster.f0tfh6g.mongodb.net/?retryWrites=true&w=majority&appName=BotGovCluster",
        "db": "govbot",
        "collection": "bocongan"
    }
    scraper = BoCongAnScraper(mongo_config, logging.getLogger(__name__))
    scraper.scrape()