from pymongo import MongoClient
import os

MONGO_URI = os.getenv("MONGO_URI")  # Ensure your .env is correctly loaded
client = MongoClient(MONGO_URI)
db = client["portfolio"]
projects_collection = db["projects"]

# Fetch and print all projects
projects = list(projects_collection.find({}, {"_id": 0}))  # Exclude `_id`
if projects:
    for project in projects:
        print(project)
else:
    print("⚠️ No projects found in MongoDB. Check GitHub fetching!")
