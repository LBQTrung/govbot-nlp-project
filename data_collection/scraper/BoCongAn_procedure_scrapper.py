import json
import logging
import requests
from bs4 import BeautifulSoup
from typing import Dict, Optional
from datetime import datetime
import os

class BoCongAnProcedureScraper:
    def __init__(self, logger):
        self.logger = logger
        
    def log_info(self, message: str):
        """Log information message"""
        self.logger.info(message)

    def log_error(self, message: str):
        """Log error message"""
        self.logger.error(message)

    def get_page_content(self, url: str) -> Optional[BeautifulSoup]:
        """Get page content using requests and return BeautifulSoup object"""
        try:
            response = requests.get(url)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'html.parser')
        except Exception as e:
            self.log_error(f"Error fetching page {url}: {str(e)}")
            return None

    def extract_text_from_row(self, row) -> str:
        """Extract text from a row's content column"""
        try:
            content = row.select_one('.col-sm-9.col-xs-12')
            if content:
                return content.get_text(strip=True)
            return ""
        except Exception:
            return ""

    def extract_table_data(self, table) -> list:
        """Extract data from a table structure and convert to list of dictionaries"""
        data = []
        try:
            rows = table.find_all('tr')
            if not rows:
                return data

            # Get headers from first row
            headers = [cell.get_text(strip=True) for cell in rows[0].find_all(['th', 'td'])]
            
            # Process data rows
            for row in rows[1:]:
                cells = row.find_all(['td', 'th'])
                if cells:
                    # Create dictionary with header as key and cell text as value
                    row_data = {headers[i]: cell.get_text(strip=True) for i, cell in enumerate(cells)}
                    data.append(row_data)
                    
        except Exception as e:
            self.log_error(f"Error extracting table data: {str(e)}")
        return data

    def scrape_procedure(self, url: str) -> Dict:
        """Scrape detailed information for a single procedure"""
        soup = self.get_page_content(url)
        if not soup:
            return {}

        procedure_data = {}
        
        # List of special fields that need table extractio
        mapping_special_fields = {
            "Thành phần hồ sơ": "thanh_phan_ho_so",
        }

        # Mapping fields to their keys  
        mapping_fields = {
            "Mã thủ tục": "ma_thu_tuc",
            "Lĩnh vực": "linh_vuc",
            "Cơ quan thực hiện": "co_quan_thuc_hien",
            "Mức độ cung cấp dịch vụ công trực tuyến": "muc_do_cung_cap_dich_vu_cong_truc_tuyen",
            "Cách thức thực hiện": "cach_thuc_thuc_hien",
            "Trình tự thực hiện": "trinh_tu_thuc_hien",
            "Thời hạn giải quyết": "thoi_han_giai_quyet",
            "Phí": "phi",
            "Yêu cầu - điều kiện": "yeu_cau_dieu_kien",
            "Biểu mẫu": "bieu_mau",
            "Kết quả thực hiện": "ket_qua_thuc_hien"
        }

        # Iterate through all info rows
        info_rows = soup.find_all('div', class_='tthc-list-item')
        for row in info_rows:
            try:
                # Get the field label
                field_label = row.select_one('.item-title').get_text(strip=True)
                
                # Check if this is a special field that needs table extraction
                if field_label in mapping_special_fields:
                    # Find the next table after this row
                    table = row.find_next('table')
                    if table:
                        procedure_data[mapping_special_fields[field_label]] = self.extract_table_data(table)
                    else:
                        procedure_data[mapping_special_fields[field_label]] = []
                
                # For regular fields, just extract text from the content column
                elif field_label in mapping_fields:
                    content = row.select_one('.tthc-list-item-detail')
                    if content:
                        # Convert field label to snake_case for the key
                        field_key = mapping_fields[field_label]
                        procedure_data[field_key] = content.get_text(strip=True)
                    else:
                        procedure_data[field_key] = ""
                        
            except Exception as e:
                self.log_error(f"Error processing row with label {field_label}: {str(e)}")
                continue

        return procedure_data


if __name__ == "__main__":
    scraper = BoCongAnProcedureScraper(logging.getLogger(__name__))
    # Example usage:
    url = "https://dichvucong.bocongan.gov.vn/bocongan/bothutuc/tthc?matt=26281"
    print(scraper.scrape_procedure(url)) 