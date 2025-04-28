# Government Procedures Data Collection System

This project is designed to collect and store administrative procedures data from Vietnamese government websites. The system consists of multiple components that work together to scrape, process, and store data efficiently.

## Project Structure

```
.
├── crawl_list.py           # Main script for collecting procedure lists
├── crawl_detail.py         # Script for collecting detailed procedure information
├── scraper/
│   ├── agency_scraper.py   # Scraper for agency-specific procedures
│   └── procedure_scraper.py # Scraper for detailed procedure information
└── logs/                   # Directory for log files
```

## Components

### 1. Agency List Collection (`crawl_list.py`)
- Collects basic information about administrative procedures from multiple government agencies
- Uses Selenium WebDriver for dynamic content scraping
- Implements multi-threading for parallel processing
- Features:
  - Configurable number of worker threads
  - Comprehensive logging system
  - MongoDB integration for data storage
  - Error handling and retry mechanisms

### 2. Detailed Procedure Collection (`crawl_detail.py`)
- Collects detailed information for each procedure
- Processes procedures in parallel using ThreadPoolExecutor
- Features:
  - Status tracking (pending, processing, done, error)
  - Automatic retry for failed procedures
  - MongoDB integration for storing detailed data
  - Comprehensive logging system

### 3. Scrapers

#### Agency Scraper (`agency_scraper.py`)
- Handles scraping of procedure lists from specific agencies
- Features:
  - Headless Chrome browser automation
  - Pagination handling
  - Data validation and cleaning
  - MongoDB integration
  - Detailed logging
  - Error handling and recovery

#### Procedure Scraper (`procedure_scraper.py`)
- Extracts detailed information from individual procedure pages
- Features:
  - BeautifulSoup for HTML parsing
  - Structured data extraction
  - Error handling and logging
  - Support for various data formats (tables, text, etc.)

## Setup Requirements

1. Python Dependencies:
   ```
   selenium
   beautifulsoup4
   pymongo
   python-dotenv
   requests
   tqdm
   ```

2. Environment Variables:
   Create a `.env` file with:
   ```
   MONGODB_URI=your_mongodb_connection_string
   ```

3. Chrome WebDriver:
   - Place ChromeDriver in `./chrome_driver/` directory
   - Ensure ChromeDriver version matches your Chrome browser version

## Usage

1. Collect Procedure Lists:
   ```bash
   python crawl_list.py
   ```

2. Collect Detailed Information:
   ```bash
   python crawl_detail.py
   ```

## Data Structure

### Basic Procedure Information
```json
{
    "ma_so": "procedure_code",
    "ten": "procedure_name",
    "co_quan_ban_hanh": "issuing_agency",
    "co_quan_thuc_hien": "implementing_agency",
    "linh_vuc": "field",
    "url": "procedure_url",
    "status": "pending|processing|done|error",
    "agency": "agency_name",
    "collected_at": "timestamp"
}
```

### Detailed Procedure Information
```json
{
    "ma_so": "procedure_code",
    "ten": "procedure_name",
    "co_quan_ban_hanh": "issuing_agency",
    "co_quan_thuc_hien": "implementing_agency",
    "linh_vuc": "field",
    "url": "procedure_url",
    "status": "pending|processing|done|error",
    "agency": "agency_name",
    "collected_at": "timestamp",
    "ma_thu_tuc": "procedure_code",
    "so_quyet_dinh": "decision_number",
    "ten_thu_tuc": "procedure_name",
    "cap_thuc_hien": "implementation_level",
    "loai_thu_tuc": "procedure_type",
    "trinh_tu_thuc_hien": "implementation_steps",
    "cach_thuc_thuc_hien": [
        {
            "Hình thức nộp": "submission_method",
            "Thời hạn giải quyết": "processing_time",
            "Phí, lệ phí": "fees",
            "Mô tả": "description"
        }
    ],
    "thanh_phan_ho_so": [
        {
            "Tên giấy tờ": "document_name",
            "Mẫu đơn, tờ khai": "form_template",
            "Số lượng": "quantity"
        }
    ],
    "doi_tuong_thuc_hien": "implementation_subject",
    "co_quan_co_tham_quyen": "authorized_agency",
    "dia_chi_tiep_nhan_hs": "document_receiving_address",
    "co_quan_duoc_uy_quyen": "authorized_organization",
    "co_quan_phoi_hop": "coordinating_agency",
    "ket_qua_thuc_hien": "implementation_result",
    "can_cu_phap_ly": [
        {
            "Số ký hiệu": "reference_number",
            "Trích yếu": "summary",
            "Ngày ban hành": "issue_date",
            "Cơ quan ban hành": "issuing_agency"
        }
    ],
    "yeu_cau_dieu_kien": "requirements_conditions",
    "tu_khoa": "keywords",
    "mo_ta": "description",
    "crawled_at": "timestamp",
    "original_id": "mongodb_object_id"
}
```

## Logging

The system maintains detailed logs in the `logs/` directory:
- `crawl_list.log`: Logs for procedure list collection
- `crawl_detail.log`: Logs for detailed procedure collection
- Agency-specific logs with timestamps

## Error Handling

- Automatic retry mechanisms for failed requests
- Status tracking for each procedure
- Comprehensive error logging
- Graceful failure handling with MongoDB connection management

## Performance Considerations

- Multi-threading for parallel processing
- Configurable number of worker threads
- Efficient MongoDB operations
- Headless browser automation
- Rate limiting and delays to prevent server overload 