import os
import re
import requests
from langchain.tools import tool
from pymongo import MongoClient

# Load environment variables
MONGO_URI = os.getenv("MONGO_URI")
GITHUB_USERNAME = os.getenv("GITHUB_USERNAME")
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

import re

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

    return parsed_data

def extract_tech(content, field):
    """Extract specific tech stack fields like Frontend, Backend, etc."""
    match = re.search(fr"- \*\*{field}:\*\* ?(.*)", content)
    return match.group(1).strip() if match and match.group(1) else "Not specified"


def update_project_in_mongodb(repo_name):
    """Force update GitHub project details in MongoDB."""
    readme_content = fetch_readme(repo_name)
    parsed_data = parse_readme(readme_content)

    if parsed_data:
        # First, unset old values to remove stale data
        projects_collection.update_one(
            {"name": repo_name},
            {"$unset": {"description": "", "tech_stack": "", "features": ""}}
        )

        # Second, set the new values
        projects_collection.update_one(
            {"name": repo_name},
            {"$set": parsed_data},
            upsert=True
        )

        print(f"✅ Forced update for project: {repo_name}")
    else:
        print(f"❌ No structured README found for {repo_name}")



@tool("github_project_search")
def search_github_projects(query: str) -> str:
    """Search GitHub projects stored in MongoDB by a keyword and update them."""
    # Fetch all projects from MongoDB
    projects = list(projects_collection.find({}, {"name": 1}))

    # Update each project's data from GitHub
    for project in projects:
        repo_name = project["name"]
        print(f"🔄 Updating {repo_name} from GitHub...")
        update_project_in_mongodb(repo_name)

    # Search again after updating
    projects = list(projects_collection.find({}, {"project_name": 1, "description": 1, "tech_stack": 1, "features": 1, "html_url": 1, "_id": 0}))

    if not projects:
        return "No projects found in the database."

    results = []
    for project in projects:
        project_name = project.get("project_name", "Unknown Project")
        project_description = project.get("description", "No description available")
        project_url = project.get("html_url", "#")
        tech_stack = project.get("tech_stack", {})
        features = project.get("features", [])

        formatted_features = "\n".join([f"- {feature}" for feature in features])

        results.append(f"""
📌 **{project_name}**
🔹 **Description:** {project_description}
🛠 **Tech Stack:** {tech_stack}
✨ **Features:**
{formatted_features}
🔗 **[View on GitHub]({project_url})**
""")

    return "\n".join(results) if results else "No matching projects found."