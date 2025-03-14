import os
import re
import requests
import logging
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
GITHUB_USERNAME = os.getenv("GITHUB_USERNAME")

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# MongoDB Connection
client = MongoClient(MONGO_URI)
db = client["portfolio"]
projects_collection = db["projects"]

def fetch_readme(repo_name):
    """Fetch the README content from GitHub."""
    url = f"https://raw.githubusercontent.com/{GITHUB_USERNAME}/{repo_name}/main/README.md"
    response = requests.get(url)

    if response.status_code == 200:
        return response.text
    return None

def parse_readme(readme_content):
    """Extract structured data from the README content."""
    if not readme_content:
        return {}

    parsed_data = {}

    # Extract Project Name
    project_name_match = re.findall(r"^# (.+)", readme_content, re.MULTILINE)
    if project_name_match:
        parsed_data["project_name"] = project_name_match[0].strip()

    # Extract Description
    description_match = re.search(r"## Description\n([\s\S]+?)(?:\n##|\Z)", readme_content)
    if description_match:
        parsed_data["description"] = description_match.group(1).strip()

    # Extract Tech Stack
    parsed_data["tech_stack"] = {
        "Frontend": extract_tech(readme_content, "Frontend"),
        "Backend": extract_tech(readme_content, "Backend"),
        "Database": extract_tech(readme_content, "Database"),
        "Hardware": extract_tech(readme_content, "Hardware"),
        "Other Tools": extract_tech(readme_content, "Other Tools"),
    }

    # Extract Features
    features_match = re.search(r"## Features\n([\s\S]+?)(?:\n##|\Z)", readme_content)
    if features_match:
        parsed_data["features"] = [line.strip("- ") for line in features_match.group(1).strip().split("\n") if line.strip()]

    # Extract Demo Link
    demo_match = re.search(r"(?i)(?:Demo Link|Live Demo):?\s*(https?://[^\s]+)", readme_content)
    parsed_data["demo_link"] = demo_match.group(1).strip() if demo_match else None

    # Extract Devpost Link
    devpost_match = re.search(r"(?i)(?:Devpost):?\s*(https?://devpost\.com/[^\s]+)", readme_content)
    parsed_data["devpost_link"] = devpost_match.group(1).strip() if devpost_match else None

    return parsed_data

def extract_tech(content, field):
    """Extract specific tech stack fields like Frontend, Backend, etc."""
    match = re.search(fr"- \*\*{field}:\*\* ?(.*)", content)
    return match.group(1).strip() if match and match.group(1) else "Not specified"

def clean_project_data():
    """Remove unnecessary metadata from all MongoDB project documents."""
    logging.info("🔄 Cleaning project data...")

    for project in projects_collection.find():
        # Keep only the relevant fields
        cleaned_data = {
            "name": project.get("name"),
            "project_name": project.get("project_name"),
            "description": project.get("description"),
            "tech_stack": project.get("tech_stack"),
            "features": project.get("features"),
            "demo_link": project.get("demo_link"),
            "devpost_link": project.get("devpost_link"),
            "embedding": project.get("embedding")  # Keep embeddings if available
        }

        # Remove any `None` values from the dictionary
        cleaned_data = {k: v for k, v in cleaned_data.items() if v is not None}

        # Update the document with only the cleaned fields
        projects_collection.update_one(
            {"_id": project["_id"]}, 
            {"$set": cleaned_data}
        )

        logging.info(f"✅ Cleaned project: {project.get('name')}")

if __name__ == "__main__":
    clean_project_data()
