import random
from pymongo import MongoClient
from scraper.BoCongAn_procedure_scrapper import BoCongAnProcedureScraper
import time
from datetime import datetime
import logging
from concurrent.futures import ThreadPoolExecutor
import dotenv
import os

dotenv.load_dotenv()

def setup_logger():
    """Setup and return a logger instance"""
    # Create logs directory if it doesn't exist
    if not os.path.exists('logs'):
        os.makedirs('logs')
        
    # Create logger
    logger = logging.getLogger('crawl_detail')
    logger.setLevel(logging.INFO)
    
    # Create handlers
    file_handler = logging.FileHandler('logs/BoCongAn_crawl_detail.log', encoding='utf-8')
    console_handler = logging.StreamHandler()
    
    # Create formatters and add it to handlers
    log_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(log_format)
    console_handler.setFormatter(log_format)
    
    # Add handlers to the logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

# MongoDB connection
client = MongoClient(os.getenv('MONGODB_URI'))
client.admin.command('ping')
db = client['govbot']
procedures_collection = db['bocongan']
detailed_procedures_collection = db['bocongan_detailed']
print("Kết nối MongoDB thành công")

def get_pending_procedures(limit=10):
    """Get multiple pending procedures"""
    return list(procedures_collection.find({'status': 'pending'}).limit(limit))

def get_processing_procedures():
    """Get all procedures that are currently being processed"""
    return list(procedures_collection.find({'status': 'processing'}))

def get_random_pending_procedure():
    """Get a random procedure with pending status"""
    return procedures_collection.find_one({'status': 'pending'})

def update_procedure_status(procedure_id, status):
    """Update the status of a procedure"""
    procedures_collection.update_one(
        {'_id': procedure_id},
        {'$set': {'status': status}}
    )

def save_detailed_procedure(procedure_data):
    """Save detailed procedure data to new collection"""
    detailed_procedures_collection.insert_one(procedure_data)

def process_procedure(procedure, logger):
    """Process a single procedure"""
    try:
        # Update status to processing
        update_procedure_status(procedure['_id'], 'processing')
        
        # Initialize scraper
        scraper = BoCongAnProcedureScraper(logger)
        
        # Get detailed information using the scrape_procedure method
        detailed_info = scraper.scrape_procedure(procedure['url'])
        
        if not detailed_info:
            raise Exception("Failed to scrape procedure details")
        
        # Combine original data with detailed info
        detailed_procedure = {
            **procedure,
            **detailed_info,
        }
        
        # Remove _id to avoid duplicate key error
        detailed_procedure.pop('_id', None)
        
        # Save to detailed collection
        save_detailed_procedure(detailed_procedure)
        
        # Update status to done
        update_procedure_status(procedure['_id'], 'done')
        
        return True
    except Exception as e:
        logging.error(f"Error processing procedure {procedure['_id']}: {str(e)}")
        update_procedure_status(procedure['_id'], 'error')
        return False

def main():
    # Setup logger
    logger = setup_logger()
    
    # Số lượng worker threads
    max_workers = 20
    
    while True:
        try:
            # Get multiple pending procedures
            procedures = get_pending_procedures(limit=max_workers)
            
            if not procedures:
                # Kiểm tra xem có procedure nào đang xử lý không
                processing_procedures = get_processing_procedures()
                if not processing_procedures:
                    logger.info("All procedures have been processed. Exiting...")
                    break
                else:
                    logger.info(f"Waiting for {len(processing_procedures)} procedures to complete...")
                    time.sleep(60)  # Wait for 1 minute before checking again
                    continue
            
            logger.info(f"Processing {len(procedures)} procedures")
            
            # Sử dụng ThreadPoolExecutor để xử lý đồng thời
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = [
                    executor.submit(process_procedure, procedure, logger)
                    for procedure in procedures
                ]
                
                # Đợi tất cả các task hoàn thành
                for future in futures:
                    future.result()
            
            # Add a small delay between batches
            time.sleep(2)
            
        except Exception as e:
            logger.error(f"Unexpected error in main loop: {str(e)}")
            time.sleep(60)  # Wait longer if there's an error

if __name__ == "__main__":
    main()
