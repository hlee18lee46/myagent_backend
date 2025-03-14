from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pymongo import MongoClient
from apscheduler.schedulers.background import BackgroundScheduler
import requests
import os
from dotenv import load_dotenv
from agent.tool_calling_agent_backup import agent  # Import your LangChain Agent
import time

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

def retry_with_delay(func, max_retries=3, delay=2):
    """Retries the Gemini API call with exponential backoff."""
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if "429" in str(e):  # Check if the error is rate limit
                wait_time = delay * (2 ** attempt)  # Exponential backoff: 2s, 4s, 8s...
                print(f"⚠️ Rate limited. Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                raise e  # Raise other errors immediately
            
# Schedule GitHub updates (Runs daily)
scheduler = BackgroundScheduler()
scheduler.add_job(fetch_github_projects, "cron", hour=0)	
scheduler.start()

# 🔹 API Route to Chat with the Agent
@app.post("/api/chat")
def chat(request: ChatRequest):
    try:
        response = retry_with_delay(lambda: agent.run(request.message))
        return {"reply": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Root Route
@app.get("/")
def root():
    return {"message": "FastAPI server is running with LangChain Agent (Google Gemini) and CORS enabled!"}
