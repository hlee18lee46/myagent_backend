import os
import re
import requests
import logging
import time
import numpy as np
from pymongo import MongoClient
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

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

# Load Sentence Transformer Model
embed_model = SentenceTransformer("all-MiniLM-L6-v2")

# Create a requests session for better performance
session = requests.Session()


def fetch_readme(repo_name, retries=3):
    """Fetch the README content from GitHub with exponential backoff."""
    url = f"https://raw.githubusercontent.com/{GITHUB_USERNAME}/{repo_name}/main/README.md"

    for attempt in range(retries):
        response = session.get(url)

        if response.status_code == 200:
            return response.text
        elif response.status_code == 403:  # GitHub API rate limit
            wait_time = 2 ** attempt
            logging.warning(f"Rate limited. Retrying in {wait_time} seconds...")
            time.sleep(wait_time)

    logging.error(f"❌ Failed to fetch README for {repo_name}")
    return None  # Return None if all retries fail


def parse_readme(readme_content):
    """Extract structured data from the README content."""
    if not readme_content:
        return {}

    parsed_data = {}

    # Extract Project Name
    project_name_match = re.findall(r"^# (.+)", readme_content, re.MULTILINE)
    parsed_data["name"] = project_name_match[0].strip() if project_name_match else "Unknown Project"

    # Extract Description
    description_match = re.search(r"## Description\n([\s\S]+?)(?:\n##|\Z)", readme_content)
    parsed_data["description"] = description_match.group(1).strip() if description_match else "No description available"

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
    parsed_data["features"] = [line.strip("- ") for line in features_match.group(1).strip().split("\n") if line.strip()] if features_match else []

    # Extract Demo & Devpost Links
    parsed_data["demo_link"] = extract_link(readme_content, "Demo Link|Live Demo")
    parsed_data["devpost_link"] = extract_link(readme_content, "Devpost")

    return parsed_data


def extract_tech(content, field):
    """Extract specific tech stack fields like Frontend, Backend, etc."""
    match = re.search(fr"- \*\*{field}:\*\* ?(.*)", content)
    return match.group(1).strip() if match and match.group(1) else "Not specified"


def extract_link(content, pattern):
    """Extract links from README."""
    match = re.search(fr"(?i)(?:{pattern}):?\s*(https?://[^\s]+)", content)
    return match.group(1).strip() if match else "No link available"


def generate_embedding(text):
    """Generate vector embedding for the given text, return empty array if no text."""
    if not text or text == "No description available":
        return []  # Avoid encoding empty text
    return embed_model.encode(text).tolist()


def update_github_projects():
    """Fetch repositories from GitHub, fetch their README files, parse them, and update MongoDB."""
    logging.info("🔄 Fetching GitHub projects...")

    url = f"https://api.github.com/users/{GITHUB_USERNAME}/repos"
    headers = {"Accept": "application/vnd.github.v3+json"}
    response = session.get(url, headers=headers)

    if response.status_code == 200:
        projects = response.json()
        logging.info(f"✅ Retrieved {len(projects)} repositories from GitHub.")

        for project in projects:
            repo_name = project.get("name")

            # Check if the project already exists to avoid redundant updates
            existing_project = projects_collection.find_one({"name": repo_name}, {"updated_at": 1})
            if existing_project and existing_project.get("updated_at") == project.get("updated_at"):
                logging.info(f"⏭ Skipping {repo_name} (Already up-to-date)")
                continue

            readme_content = fetch_readme(repo_name)
            parsed_data = parse_readme(readme_content)

            if parsed_data:
                # Add GitHub metadata (Minimal)
                parsed_data.update({
                    "html_url": project.get("html_url"),
                    "language": project.get("language"),
                    "updated_at": project.get("updated_at"),
                })

                # Generate embedding only if description exists
                embedding = generate_embedding(parsed_data.get("description", ""))
                if embedding:
                    parsed_data["embedding"] = embedding

                # Convert NumPy arrays to lists before inserting into MongoDB
                if "embedding" in parsed_data and isinstance(parsed_data["embedding"], np.ndarray):
                    parsed_data["embedding"] = parsed_data["embedding"].tolist()

                # Update MongoDB
                projects_collection.update_one(
                    {"name": repo_name},
                    {"$set": parsed_data},
                    upsert=True
                )
                logging.info(f"✅ Updated project: {repo_name}")
            else:
                logging.warning(f"⚠️ No structured README found for {repo_name}")

    elif response.status_code == 403:
        logging.error("❌ GitHub API rate limit exceeded. Try again later.")
    else:
        logging.error(f"❌ Failed to fetch GitHub projects. Status Code: {response.status_code}")


if __name__ == "__main__":
    update_github_projects()
