from agency_scraper import AgencyScraper

def main():
    agency_name = "Bộ Công an"
    scraper = AgencyScraper(agency_name)
    scraper.scrape()
    scraper.save_to_json() # Only for testing and showing the sample data

if __name__ == "__main__":
    main()

