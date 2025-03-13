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

    # Extract Project Name - Take the first line after "#"
    project_name_match = re.findall(r"^# (.+)", readme_content, re.MULTILINE)
    if project_name_match:
        parsed_data["project_name"] = project_name_match[0].strip()

    # Extract Description - Take the first paragraph after "## Description"
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

    # Extract Demo Link (if available)
    demo_match = re.search(r"(?i)(?:Demo Link|Live Demo):?\s*(https?://[^\s]+)", readme_content)
    if demo_match:
        parsed_data["demo_link"] = demo_match.group(1).strip()

    # Extract Devpost Link (if available)
    devpost_match = re.search(r"(?i)(?:Devpost):?\s*(https?://devpost\.com/[^\s]+)", readme_content)
    if devpost_match:
        parsed_data["devpost_link"] = devpost_match.group(1).strip()

    return parsed_data

def extract_tech(content, field):
    """Extract specific tech stack fields like Frontend, Backend, etc."""
    match = re.search(fr"- \*\*{field}:\*\* ?(.*)", content)
    return match.group(1).strip() if match and match.group(1) else "Not specified"

def update_github_projects():
    """Fetch repositories from GitHub, fetch their README files, parse them, and update MongoDB."""
    logging.info("🔄 Fetching GitHub projects...")

    url = f"https://api.github.com/users/{GITHUB_USERNAME}/repos"
    headers = {"Accept": "application/vnd.github.v3+json"}
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        projects = response.json()
        logging.info(f"✅ Retrieved {len(projects)} repositories from GitHub.")

        for project in projects:
            repo_name = project.get("name")
            readme_content = fetch_readme(repo_name)
            parsed_data = parse_readme(readme_content)

            if parsed_data:
                # Add project metadata from GitHub API
                parsed_data.update({
                    "name": repo_name,
                    "html_url": project.get("html_url"),
                    "created_at": project.get("created_at"),
                    "updated_at": project.get("updated_at"),
                    "language": project.get("language"),
                })

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
