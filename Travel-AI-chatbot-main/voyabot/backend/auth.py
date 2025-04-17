import hashlib
from pymongo import MongoClient

# MongoDB Atlas connection string
client = MongoClient("mongodb+srv://shirinfathima003:ANhx61RJQ47TKc33@cluster1.9dyv4.mongodb.net/?retryWrites=true&w=majority&appName=Cluster1")
db = client["voyabot_db"]
users_collection = db["users"]

def hash_password(password):
    """Hashes a password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()

def create_user(username, password):
    """Creates a new user."""
    if users_collection.find_one({"username": username}):
        return False, "Username already exists."
    hashed_password = hash_password(password)
    users_collection.insert_one({"username": username, "password": hashed_password})
    return True, "User created successfully."

def authenticate_user(username, password):
    """Authenticates a user."""
    hashed_password = hash_password(password)
    user = users_collection.find_one({"username": username, "password": hashed_password})
    return user is not None
