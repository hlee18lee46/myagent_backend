import random
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException

from pydantic import BaseModel
from langchain.tools import Tool
from tools.github_search_tool import (
    search_github_projects_by_name,
    search_github_projects_by_frontend,
    search_github_projects_by_backend,
    search_github_projects_by_database,
    search_github_projects_by_hardware
)
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
import os
import requests
from dotenv import load_dotenv
from agent.tool_calling_agent import agent as tool_calling_agent


# Load environment variables
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
GITHUB_USERNAME = os.getenv("GITHUB_USERNAME")

# Initialize FastAPI
app = FastAPI()

# Enable CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (or specify frontend URL for security)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB Connection
client = MongoClient(MONGO_URI)
db = client["portfolio"]
projects_collection = db["projects"]

# Define Request Model
class ChatRequest(BaseModel):
    message: str

# Greeting responses
greetings = ["Hello! How can I help you?", "Hi there! Need assistance with a project?", "Hey! What are you looking for?"]

# Fallback responses
fallback_responses = ["I'm not sure how to respond to that. Can you be more specific?", "I couldn't find anything relevant.", "Try rephrasing your query."]

# 🔹 Define pre-set rule-based tools
def rule_based_tool_selector(user_input):
    user_input_lower = user_input.lower()

    if any(greet in user_input_lower for greet in ["hi", "hello", "hey", "greetings"]):
        return "greeting"
    elif "frontend" in user_input_lower:
        return "frontend_search"
    elif "backend" in user_input_lower:
        return "backend_search"
    elif "database" in user_input_lower:
        return "database_search"
    elif "hardware" in user_input_lower:
        return "hardware_search"
    #elif "project" in user_input_lower or "github" in user_input_lower:
        #return "project_search"
    else:
        return None  # Let LLM handle it

# 🔹 Rule-based agent logic
def rule_based_agent(user_input):
    selected_tool_name = rule_based_tool_selector(user_input)

    if selected_tool_name == "greeting":
        return random.choice(["Hello! My name is Han", "Hey there! How can I help?", "Hi! Need help with something?", "My name is Han. How can I help?"])
    elif selected_tool_name == "frontend_search":
        return search_github_projects_by_frontend(user_input)
    elif selected_tool_name == "backend_search":
        return search_github_projects_by_backend(user_input)
    elif selected_tool_name == "database_search":
        return search_github_projects_by_database(user_input)
    elif selected_tool_name == "hardware_search":
        return search_github_projects_by_hardware(user_input)
    elif selected_tool_name == "project_search":
        return search_github_projects_by_name(user_input)

    # 🔹 No rule-based tool found → Use LLM-powered tool-calling agent
    print("⚠️ No rule-based tool found. Switching to `tool_calling_agent`.")
    return tool_calling_agent.run(user_input)

# API Endpoint for Chat
@app.post("/api/chat")
def chat(request: ChatRequest):
    try:
        query = request.message.strip()
        print(f"🔍 Received Query: {query}")

        # Use Rule-Based Agent
        response = rule_based_agent(query)

        print(f"📂 Response: {response}")

        return {"reply": response}
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Root Route
@app.get("/")
def root():
    return {"message": "FastAPI server is running with Rule-Based Agent and MongoDB search!"}
