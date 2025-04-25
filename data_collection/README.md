# Agency Data Scraper

A project for collecting public service data from dichvucong.gov.vn for specific agencies.

## Directory Structure

```
.
├── agency_scraper.py    # Main script for data collection
├── chrome_driver/       # Directory containing Chrome WebDriver
├── data/               # Directory for collected data (JSON)
└── logs/               # Directory for log files
```

## Requirements

- Python 3.7+
- Chrome WebDriver
- Python libraries:
  - selenium
  - tqdm

## Installation

1. Install required libraries:
```bash
pip install selenium tqdm
```

2. Download the appropriate Chrome WebDriver for your Chrome version and place it in the `chrome_driver/` directory

## Usage

1. Create necessary directories:
```bash
mkdir data logs
```

2. Run the script with the agency name to collect data:
```python
from agency_scraper import AgencyScraper

# Initialize scraper with agency name
scraper = AgencyScraper("Agency Name")

# Start data collection
scraper.scrape()

# Save data to JSON file
scraper.save_to_json()
```

## Collected Data

For each public service, the following data is collected:
- Service code
- Service name
- Issuing agency
- Implementing agency
- Field/domain
- Detail URL

Data is saved in JSON format in the `data/` directory with filename format: `[Agency_Name]_data.json`

## Logging

The data collection process is logged in the `logs/` directory with filename format: `[Agency_Name]_[Timestamp].log` 