from langchain.tools import tool
from pymongo import MongoClient
import os

# Load environment variables
MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["portfolio"]
projects_collection = db["projects"]

@tool("github_project_search")
def search_github_projects(query: str) -> str:
    """Search GitHub projects stored in MongoDB by a keyword."""
    projects = list(projects_collection.find({}, {"name": 1, "description": 1, "html_url": 1, "_id": 0}))

    if not projects:
        return "No projects found in the database."

    results = []
    for project in projects:
        project_name = project.get("name", "Unknown Project")
        project_description = project.get("description") or "No description available"
        project_url = project.get("html_url", "#")

        if query.lower() in project_name.lower() or query.lower() in project_description.lower():
            results.append(f"Project: {project_name} - {project_description} [🔗]({project_url})")

    return "\n".join(results) if results else "No matching projects found."
