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

class AgencyScraper:
    def __init__(self, agency_name: str):
        self.agency_name = agency_name
        self.base_url = "https://dichvucong.gov.vn/p/home/dvc-tthc-thu-tuc-hanh-chinh.html"
        self.selectors = {
            "advanced_search": ".box-search .adv",
            "agency_select": "#select2-select-implementation-agency-container",
            "agency_options": ".select2-results__option",
            "search_button": "#btn-search",
            "service_links": "a:has(span.link.thick)",
            "current_page": "li.page.active a",
            "next_page": "li.page a"
        }
        self.setup_driver()
        self.collected_data = []
        self.setup_logger()

    def setup_logger(self):
        """Thiết lập logger"""
        # Tạo tên file log dựa trên tên agency và thời gian
        log_filename = f"logs/{self.agency_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        # Tạo thư mục logs nếu chưa tồn tại
        import os
        if not os.path.exists('logs'):
            os.makedirs('logs')
            
        # Cấu hình logger
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_filename, encoding='utf-8'),
                logging.StreamHandler()  # Hiển thị log trên console
            ]
        )
        self.logger = logging.getLogger(__name__)

    def log_info(self, message: str):
        """Ghi log thông tin"""
        self.logger.info(message)

    def log_error(self, message: str):
        """Ghi log lỗi"""
        self.logger.error(message)

    def setup_driver(self):
        """Setup Chrome WebDriver with appropriate options"""
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        try:
            service = Service("./chrome_driver/chromedriver.exe")
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

    def select_agency(self):
        """Chọn agency cụ thể"""
        try:
            # Click vào nút tìm kiếm nâng cao
            self.click_element(self.selectors["advanced_search"])
            time.sleep(2)

            # Click vào select box cơ quan
            self.click_element(self.selectors["agency_select"])
            time.sleep(1)

            # Chọn agency
            agency_elements = self.driver.find_elements(By.CSS_SELECTOR, self.selectors["agency_options"])
            for elem in agency_elements:
                if elem.text == self.agency_name:
                    elem.click()
                    break

            # Click nút search
            self.click_element(self.selectors["search_button"])
            time.sleep(3)  # Đợi kết quả load

            # Chọn số hàng hiển thị tối đa
            try:
                # Click vào select box số hàng
                self.click_element("#paginationRecsPerPage")
                time.sleep(1)

                # Chọn option có giá trị 50
                option = self.driver.find_element(By.CSS_SELECTOR, "#paginationRecsPerPage option[value='50']")
                option.click()
                time.sleep(2)  # Đợi trang load lại với số hàng mới
            except Exception as e:
                print(f"Error selecting records per page: {str(e)}")

        except Exception as e:
            print(f"Error selecting agency {self.agency_name}: {str(e)}")
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

    def collect_page_data(self):
        """Thu thập dữ liệu từ trang hiện tại"""
        try:
            # Lấy tất cả các hàng trong bảng
            rows = self.driver.find_elements(By.CSS_SELECTOR, "tbody tr")
            
            for index, row in enumerate(rows):
                try:
                    if index == 0:
                        continue
                    
                    service_info = {
                        "ma_so": row.find_element(By.CSS_SELECTOR, 'td[data-title="Mã số"]').text,
                        "ten": row.find_element(By.CSS_SELECTOR, 'td[data-title="Tên"]').text,
                        "co_quan_ban_hanh": row.find_element(By.CSS_SELECTOR, 'td[data-title="Cơ quan ban hành"]').text,
                        "co_quan_thuc_hien": row.find_element(By.CSS_SELECTOR, 'td[data-title="Cơ quan thực hiện"]').text,
                        "linh_vuc": row.find_element(By.CSS_SELECTOR, 'td[data-title="Lĩnh vực"]').text,
                        "url": row.find_element(By.CSS_SELECTOR, 'td[data-title="Mã số"] a').get_attribute("href")
                    }
                    print(service_info)
                    self.collected_data.append(service_info)
                except Exception as e:
                    print(f"Error collecting row data: {str(e)}")
                    continue
                    
        except Exception as e:
            print(f"Error collecting page data: {str(e)}")

    def scrape(self):
        """Thực hiện quá trình thu thập dữ liệu"""
        try:
            self.log_info(f"Bắt đầu thu thập dữ liệu cho {self.agency_name}")
            self.driver.get(self.base_url)
            self.wait_for_page_load()
            
            # Chọn agency và tìm kiếm
            self.select_agency()
            
            # Thu thập dữ liệu từ tất cả các trang
            total_pages = 0
            while True:
                current_page = self.get_current_page()
                total_pages = max(total_pages, current_page)
                self.log_info(f"Đang thu thập trang {current_page}")
                
                # Đếm số bản ghi trước khi thu thập
                records_before = len(self.collected_data)
                
                # Thu thập dữ liệu
                self.collect_page_data()
                
                # Đếm số bản ghi sau khi thu thập
                records_after = len(self.collected_data)
                records_collected = records_after - records_before
                
                self.log_info(f"Trang {current_page}: Thu thập được {records_collected} bản ghi")
                
                if not self.has_next_page():
                    break
                    
                if not self.go_to_next_page():
                    break
            
            self.log_info(f"Hoàn thành thu thập dữ liệu cho {self.agency_name}")
            self.log_info(f"Tổng số trang: {total_pages}")
            self.log_info(f"Tổng số bản ghi thu thập được: {len(self.collected_data)}")
            
        except Exception as e:
            self.log_error(f"Lỗi trong quá trình thu thập dữ liệu: {str(e)}")
        finally:
            self.driver.quit()

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
