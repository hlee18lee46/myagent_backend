from langchain.agents import initialize_agent, AgentType
from langchain.tools import Tool
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
import sys
import os

# Add the parent directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
# Now import the tool
from tools.github_search_tool import search_github_projects


# Load Google Gemini API Key
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Initialize the Gemini LLM
llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-pro",  # Updated model name
    google_api_key=GEMINI_API_KEY
)

# Define the tools the agent can use
tools = [
    Tool(
        name="GitHub Search",
        func=search_github_projects,
        description="Search GitHub projects stored in MongoDB by a keyword."
    )
]

# Create the tool-calling agent
agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True
)

response = agent.run("Find projects related to AI")
print(response)
