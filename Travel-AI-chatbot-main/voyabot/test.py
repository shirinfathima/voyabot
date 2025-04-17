from pymongo import MongoClient

# MongoDB Atlas connection string
client = MongoClient("mongodb+srv://shirinfathima003:ANhx61RJQ47TKc33@cluster1.9dyv4.mongodb.net/?retryWrites=true&w=majority&appName=Cluster1")
db = client["voyabot_db"]
print("Connected to the database")
