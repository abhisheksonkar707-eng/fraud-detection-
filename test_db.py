import os
import urllib.parse
import certifi
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")

if not MONGO_URI or "<db_password>" in MONGO_URI:
    password = input("Please enter your MongoDB database password: ").strip()
    encoded_pass = urllib.parse.quote_plus(password)
    MONGO_URI = f"mongodb://abhisheksonkar707_db_user:{encoded_pass}@ac-uxpr2iy-shard-00-00.dmzepa5.mongodb.net:27017,ac-uxpr2iy-shard-00-01.dmzepa5.mongodb.net:27017,ac-uxpr2iy-shard-00-02.dmzepa5.mongodb.net:27017/?ssl=true&replicaSet=atlas-nprrlv-shard-0&authSource=admin&appName=Cluster0&compressors=zlib"

try:
    print("Connecting to MongoDB Atlas...")
    client = MongoClient(
        MONGO_URI,
        tlsCAFile=certifi.where(),
        serverSelectionTimeoutMS=5000,
        connectTimeoutMS=5000
    )
    client.admin.command("ping")
    print("✅ Connected successfully to MongoDB Atlas!")
    client.close()
except Exception as e:
    print("❌ The following error occurred:", e)
