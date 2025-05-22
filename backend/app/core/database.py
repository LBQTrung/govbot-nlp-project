from pymongo import MongoClient
from .config import settings

class Database:
    client: MongoClient = None

db = Database()

def get_database():
    return db.client[settings.DATABASE_NAME]

def connect_to_mongo():
    try:
        db.client = MongoClient(settings.MONGODB_URL)
        # Ping the server
        db.client.admin.command('ping')
        print("✅ Successfully connected to MongoDB!")
        print(f"📦 Database: {settings.DATABASE_NAME}")
    except Exception as e:
        print("❌ Failed to connect to MongoDB!")
        print(f"Error: {str(e)}")
        raise e
