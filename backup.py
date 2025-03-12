from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pymongo import MongoClient
from apscheduler.schedulers.background import BackgroundScheduler
import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
GITHUB_USERNAME = os.getenv("GITHUB_USERNAME")

# Initialize FastAPI
app = FastAPI()

# 🔹 Enable CORS to allow frontend to communicate with backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (or specify frontend URL for security)
    allow_credentials=True,
    allow_methods=["*"],  # Allows GET, POST, OPTIONS, etc.
    allow_headers=["*"],  # Allows all headers
)

# MongoDB Connection
client = MongoClient(MONGO_URI)
db = client["portfolio"]
projects_collection = db["projects"]

# Define Request Model
class ChatRequest(BaseModel):
    message: str

# Function to fetch GitHub projects
def fetch_github_projects():
    url = f"https://api.github.com/users/{GITHUB_USERNAME}/repos"
    headers = {"Accept": "application/vnd.github.v3+json"}
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        projects_collection.delete_many({})  # Clear old data
        projects_collection.insert_many(response.json())  # Insert new data
        print("✅ GitHub projects updated successfully.")
    else:
        print("❌ Failed to fetch GitHub projects.")

# Schedule GitHub updates (Runs daily)
scheduler = BackgroundScheduler()
scheduler.add_job(fetch_github_projects, "interval", days=1)
scheduler.start()

# Simple Keyword-Based Search
"""
def search_projects(query):
    projects = list(projects_collection.find({}, {"name": 1, "description": 1, "_id": 0}))

    # Find matching projects
    results = []
    for project in projects:
        if query.lower() in project["name"].lower() or query.lower() in project["description"].lower():
            results.append(f"Project: {project['name']} - {project['description']}")

    return results if results else ["No matching projects found."]
"""

def search_projects(query):
    projects = list(projects_collection.find({}, {"name": 1, "description": 1, "_id": 0}))

    if not projects:
        return ["No projects found in the database."]

    results = []
    for project in projects:
        # Ensure missing values are replaced with default strings
        project_name = project.get("name") or "Unknown Project"
        project_description = project.get("description") or "No description available"

        # Convert to lowercase safely
        if query.lower() in project_name.lower() or query.lower() in project_description.lower():
            results.append(f"Project: {project_name} - {project_description}")

    return results if results else ["No matching projects found."]


# API Route to Chat with the Agent
@app.post("/api/chat")
def chat(request: ChatRequest):
    try:
        response = search_projects(request.message)
        return {"reply": "\n".join(response)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Root Route
@app.get("/")
def root():
    return {"message": "FastAPI server is running with CORS enabled!"}
