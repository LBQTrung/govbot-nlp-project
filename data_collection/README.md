# Data Collection Project for Administrative Procedures

This project collects data about administrative procedures from the Vietnamese public service portal.

## Setup

1. Install Python 3.8 or higher
2. Install required packages:
```bash
pip install -r requirements.txt
```

## Usage

Run the data collection script:
```bash
python collect_links.py
```

The script will:
1. Open the public service portal
2. Collect data from all agencies
3. Save the results to `services_data.json`

## Output Format

The collected data will be saved in JSON format with the following structure:
```json
[
  {
    "ma_so": "procedure_code",
    "ten": "procedure_name",
    "co_quan_ban_hanh": "issuing_agency",
    "co_quan_thuc_hien": "implementing_agency",
    "linh_vuc": "field",
    "url": "procedure_url"
  }
]
```

## Notes

- The script runs in headless mode by default
- Progress is shown using a progress bar
- Errors for individual agencies are logged but don't stop the collection process
- The script includes appropriate waiting times to handle page loading 