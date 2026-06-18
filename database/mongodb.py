import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

mongo_uri = os.getenv("MONGO_URI")

if not mongo_uri:
    raise Exception("MONGO_URI not found. Check your .env file.")

client = MongoClient(mongo_uri)

db = client["puddle_db"]
users_collection = db["users"]
notes_collection = db["notes"]