import os
import requests
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MongoDB Connection
MONGO_URI = os.getenv("MONGO_URI")
GITHUB_USERNAME = os.getenv("GITHUB_USERNAME")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")  # Optional for rate limits

# Ensure MongoDB is connected
client = MongoClient(MONGO_URI)
db = client["portfolio"]
projects_collection = db["projects"]

# Function to fetch GitHub projects
"""



def fetch_github_projects():
    url = f"https://api.github.com/users/{GITHUB_USERNAME}/repos"
    headers = {
        "Accept": "application/vnd.github.v3+json"
    }
    
    # If a GitHub token is set, use it to avoid rate limits
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        projects = response.json()

        if not projects:
            print("⚠️ No repositories found for this GitHub user.")
            return

        # Clear old data and insert new projects
        projects_collection.delete_many({})
        projects_collection.insert_many(projects)

        print(f"✅ Successfully added {len(projects)} projects to MongoDB!")
    else:
        print(f"❌ Failed to fetch GitHub projects. Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        """

def fetch_github_projects():
    url = f"https://api.github.com/users/{GITHUB_USERNAME}/repos"
    headers = {"Accept": "application/vnd.github.v3+json"}
    
    # If using a GitHub token (to prevent rate limits)
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        projects_collection.delete_many({})  # Clear old data
        projects = response.json()

        # Fetch README if description is missing
        for project in projects:
            if project.get("description") is None:
                repo_name = project["name"]
                readme_url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{repo_name}/readme"
                readme_response = requests.get(readme_url, headers=headers)

                if readme_response.status_code == 200:
                    readme_data = readme_response.json()
                    readme_content = readme_data.get("content", "")
                    
                    if readme_content:
                        import base64
                        decoded_readme = base64.b64decode(readme_content).decode("utf-8")
                        first_lines = "\n".join(decoded_readme.split("\n")[:3])  # Get first 3 lines
                        project["description"] = first_lines if first_lines else "No description available"
                    else:
                        project["description"] = "No description available"
                else:
                    project["description"] = "No description available"

        projects_collection.insert_many(projects)  # Insert updated data
        print("✅ GitHub projects updated with descriptions from README!")
    else:
        print(f"❌ Failed to fetch GitHub projects. Status Code: {response.status_code}")


# Run the function manually
if __name__ == "__main__":
    print("🔄 Fetching GitHub projects and storing them in MongoDB...")
    fetch_github_projects()
