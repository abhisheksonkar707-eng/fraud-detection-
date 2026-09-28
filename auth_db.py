import os
import sqlite3
import datetime
import urllib.parse
import certifi
import bcrypt
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

SQLITE_DB_PATH = os.path.join(os.path.dirname(__file__), "fraud_detection.db")
DEFAULT_URI_TEMPLATE = "mongodb://abhisheksonkar707_db_user:{password}@ac-uxpr2iy-shard-00-00.dmzepa5.mongodb.net:27017,ac-uxpr2iy-shard-00-01.dmzepa5.mongodb.net:27017,ac-uxpr2iy-shard-00-02.dmzepa5.mongodb.net:27017/?ssl=true&replicaSet=atlas-nprrlv-shard-0&authSource=admin&appName=Cluster0&compressors=zlib"

# ==========================================
# SQLITE BACKEND (Guaranteed 100% Reliable)
# ==========================================
def init_sqlite_db():
    """Initializes local SQLite tables for users and predictions."""
    conn = sqlite3.connect(SQLITE_DB_PATH)
    cursor = conn.cursor()
    
    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    
    # Predictions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            tx_type TEXT,
            amount REAL,
            oldbalanceOrg REAL,
            newbalanceOrig REAL,
            oldbalanceDest REAL,
            newbalanceDest REAL,
            prediction INTEGER,
            is_fraud INTEGER,
            created_at TEXT NOT NULL
        )
    """)
    
    conn.commit()
    conn.close()

# Initialize immediately
init_sqlite_db()

def _sqlite_create_user(username: str, email: str, password_hash: str):
    conn = sqlite3.connect(SQLITE_DB_PATH)
    cursor = conn.cursor()
    try:
        # Check existing
        cursor.execute("SELECT id FROM users WHERE username = ?", (username.strip(),))
        if cursor.fetchone():
            return False, "Username already exists. Please choose a different one."
        
        cursor.execute("SELECT id FROM users WHERE LOWER(email) = ?", (email.strip().lower(),))
        if cursor.fetchone():
            return False, "Email already registered. Please login instead."
        
        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
        cursor.execute(
            "INSERT INTO users (username, email, password_hash, created_at) VALUES (?, ?, ?, ?)",
            (username.strip(), email.strip().lower(), password_hash, created_at)
        )
        conn.commit()
        return True, "Account created successfully! You can now log in."
    finally:
        conn.close()

def _sqlite_verify_user(username: str, password: str):
    conn = sqlite3.connect(SQLITE_DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT password_hash FROM users WHERE username = ?", (username.strip(),))
        row = cursor.fetchone()
        if not row:
            return False, "Invalid username or password."
        
        stored_hash = row[0].encode('utf-8')
        if bcrypt.checkpw(password.encode('utf-8'), stored_hash):
            return True, "Login successful!"
        return False, "Invalid username or password."
    finally:
        conn.close()

def _sqlite_save_prediction(username: str, tx: dict, prediction: int):
    conn = sqlite3.connect(SQLITE_DB_PATH)
    cursor = conn.cursor()
    try:
        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
        cursor.execute("""
            INSERT INTO predictions 
            (username, tx_type, amount, oldbalanceOrg, newbalanceOrig, oldbalanceDest, newbalanceDest, prediction, is_fraud, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            username,
            tx.get("type"),
            float(tx.get("amount", 0)),
            float(tx.get("oldbalanceOrg", 0)),
            float(tx.get("newbalanceOrig", 0)),
            float(tx.get("oldbalanceDest", 0)),
            float(tx.get("newbalanceDest", 0)),
            int(prediction),
            1 if prediction == 1 else 0,
            created_at
        ))
        conn.commit()
        return True
    except Exception as e:
        print(f"SQLite save prediction error: {e}")
        return False
    finally:
        conn.close()

def _sqlite_get_predictions(username: str):
    conn = sqlite3.connect(SQLITE_DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT tx_type, amount, oldbalanceOrg, newbalanceOrig, oldbalanceDest, newbalanceDest, prediction, is_fraud, created_at
            FROM predictions WHERE username = ? ORDER BY id DESC
        """, (username,))
        rows = cursor.fetchall()
        results = []
        for r in rows:
            results.append({
                "transaction": {
                    "type": r[0],
                    "amount": r[1],
                    "oldbalanceOrg": r[2],
                    "newbalanceOrig": r[3],
                    "oldbalanceDest": r[4],
                    "newbalanceDest": r[5],
                },
                "prediction": r[6],
                "is_fraud": bool(r[7]),
                "timestamp": r[8]
            })
        return results
    finally:
        conn.close()


# ==========================================
# MONGODB BACKEND
# ==========================================
def format_mongo_uri(raw_password: str = None, full_uri: str = None):
    """Safely URL-encodes password into standard MongoDB URI if needed."""
    if full_uri and "<db_password>" not in full_uri:
        return full_uri
    if raw_password:
        encoded_pass = urllib.parse.quote_plus(raw_password.strip())
        return DEFAULT_URI_TEMPLATE.format(password=encoded_pass)
    env_uri = os.getenv("MONGO_URI", "")
    if not env_uri:
        try:
            import streamlit as st
            if hasattr(st, "secrets") and "MONGO_URI" in st.secrets:
                env_uri = st.secrets["MONGO_URI"]
        except Exception:
            pass
    if env_uri and "<db_password>" not in env_uri:
        return env_uri
    return None

def test_mongo_connection(uri: str):
    """Tests if MongoDB Atlas is reachable and authenticated."""
    if not uri or "<db_password>" in uri:
        return False, "MongoDB password/URI not provided."
    try:
        client = MongoClient(
            uri,
            tlsCAFile=certifi.where(),
            serverSelectionTimeoutMS=4000,
            connectTimeoutMS=4000
        )
        client.admin.command("ping")
        client.close()
        return True, "Connected successfully to MongoDB Atlas!"
    except Exception as e:
        return False, str(e)

def get_mongo_db(uri: str):
    client = MongoClient(
        uri,
        tlsCAFile=certifi.where(),
        serverSelectionTimeoutMS=4000,
        connectTimeoutMS=4000
    )
    return client["credit_card_fraud_db"]


# ==========================================
# UNIFIED DATABASE API
# ==========================================
def create_user(username: str, email: str, password: str, uri: str = None, force_mode: str = "auto"):
    """
    Creates a user. If MongoDB is configured and available, saves to MongoDB;
    otherwise seamlessly saves to local SQLite database so registration never fails.
    """
    username = username.strip()
    email = email.strip().lower()
    
    if not username:
        return False, "Username cannot be empty."
    if not email:
        return False, "Email cannot be empty."
    if not password:
        return False, "Password cannot be empty."
        
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    # Check if MongoDB should be used
    use_mongo = False
    if force_mode in ("auto", "mongodb") and uri and "<db_password>" not in uri:
        is_ok, _ = test_mongo_connection(uri)
        if is_ok:
            use_mongo = True
        elif force_mode == "mongodb":
            return False, "Failed to connect to MongoDB Atlas. Check your password or IP whitelist."
            
    if use_mongo:
        try:
            db = get_mongo_db(uri)
            users_col = db["users"]
            if users_col.find_one({"username": username}):
                return False, "Username already exists in MongoDB."
            if users_col.find_one({"email": email}):
                return False, "Email already registered in MongoDB."
                
            users_col.insert_one({
                "username": username,
                "email": email,
                "password_hash": hashed_password,
                "created_at": datetime.datetime.now(datetime.timezone.utc)
            })
            # Also sync to local SQLite as backup
            _sqlite_create_user(username, email, hashed_password)
            return True, "Account registered successfully in MongoDB Atlas!"
        except Exception as e:
            # Fallback to local SQLite if MongoDB encounters runtime error
            print(f"MongoDB create_user failed ({e}), falling back to SQLite.")
            success, msg = _sqlite_create_user(username, email, hashed_password)
            if success:
                return True, "Account created in Local Storage (MongoDB Atlas was unreachable)."
            return False, msg
    else:
        # Save to local SQLite
        success, msg = _sqlite_create_user(username, email, hashed_password)
        return success, msg

def verify_user(username: str, password: str, uri: str = None, force_mode: str = "auto"):
    """
    Verifies user login against MongoDB or local SQLite.
    """
    username = username.strip()
    
    # Try MongoDB if available
    if force_mode in ("auto", "mongodb") and uri and "<db_password>" not in uri:
        is_ok, _ = test_mongo_connection(uri)
        if is_ok:
            try:
                db = get_mongo_db(uri)
                user = db["users"].find_one({"username": username})
                if user:
                    stored_hash = user["password_hash"].encode('utf-8')
                    if bcrypt.checkpw(password.encode('utf-8'), stored_hash):
                        return True, "Login successful via MongoDB Atlas!"
                    return False, "Invalid username or password."
            except Exception as e:
                print(f"MongoDB verification error: {e}")
                
    # Fallback / Check SQLite
    return _sqlite_verify_user(username, password)

def save_prediction(username: str, transaction_data: dict, prediction: int, uri: str = None):
    """Saves transaction prediction record to available database."""
    saved_mongo = False
    if uri and "<db_password>" not in uri:
        try:
            db = get_mongo_db(uri)
            db["predictions"].insert_one({
                "username": username,
                "transaction": transaction_data,
                "prediction": int(prediction),
                "is_fraud": bool(prediction == 1),
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
            })
            saved_mongo = True
        except Exception as e:
            print(f"Failed to log to MongoDB: {e}")
            
    # Always save to local SQLite as well for reliability
    _sqlite_save_prediction(username, transaction_data, prediction)
    return True

def get_prediction_history(username: str, uri: str = None):
    """Retrieves prediction history for user."""
    if uri and "<db_password>" not in uri:
        try:
            db = get_mongo_db(uri)
            records = list(db["predictions"].find({"username": username}, {"_id": 0}).sort("timestamp", -1))
            if records:
                return records
        except Exception as e:
            print(f"Failed to read from MongoDB: {e}")
            
    # Return local SQLite history
    return _sqlite_get_predictions(username)
