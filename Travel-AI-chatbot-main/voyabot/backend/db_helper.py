from pymongo import MongoClient

# MongoDB Atlas connection string (replace <db_password> with your actual password)
client = MongoClient("mongodb+srv://shirinfathima003:ANhx61RJQ47TKc33@cluster1.9dyv4.mongodb.net/?retryWrites=true&w=majority&appName=Cluster1")
db = client["voyabot_db"]
chat_collection = db["chat_history"]

def save_message(username, role, content):
    """Save a message to the database."""
    chat_collection.insert_one({"username": username, "role": role, "content": content})

def get_chat_history(username):
    """Retrieve chat history for a specific user."""
    return list(chat_collection.find({"username": username}))
