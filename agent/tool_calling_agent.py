from langchain.agents import initialize_agent, AgentType
from langchain.tools import Tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chat_models import ChatOpenAI
from dotenv import load_dotenv
import sys
import os

# Add the parent directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import tools
from tools.github_search_tool import (
    search_github_projects_by_name,
    search_github_projects_by_frontend,
    search_github_projects_by_backend,
    search_github_projects_by_database,
    search_github_projects_by_hardware
)

# Load API Keys
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# 🔹 Initialize Google Gemini LLM
llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-pro",  
    google_api_key=GEMINI_API_KEY,
)

# 🔹 Initialize OpenAI GPT-4-turbo as a fallback LLM
fallback_llm = ChatOpenAI(
    model_name="gpt-4-turbo",  
    openai_api_key=OPENAI_API_KEY,
    temperature=0.7,
    max_tokens=4096
)

# 🔹 Define the tools the agent can use
tools = [
    Tool(
        name="GitHub Search by Name",
        func=search_github_projects_by_name,
        description="Search GitHub projects stored in MongoDB by name. Provide project name, description, features, GitHub, demo link, and Devpost."
    ),
    Tool(
        name="GitHub Search by Frontend",
        func=search_github_projects_by_frontend,
        description="Search GitHub projects stored in MongoDB that use a specific frontend technology."
    ),
    Tool(
        name="GitHub Search by Backend",
        func=search_github_projects_by_backend,
        description="Search GitHub projects stored in MongoDB that use a specific backend technology."
    ),
    Tool(
        name="GitHub Search by Database",
        func=search_github_projects_by_database,
        description="Search GitHub projects stored in MongoDB by the database technology used."
    ),
    Tool(
        name="GitHub Search by Hardware",
        func=search_github_projects_by_hardware,
        description="Search GitHub projects stored in MongoDB that use a specific hardware component."
    )
]

# 🔹 Create the tool-calling agent with LLM fallback
agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,
    handle_parsing_errors=True  # Ensures robust error handling
)

# 🔹 Define a function that decides whether to use tools or fallback to LLM
def agent_with_fallback(user_input):
    """Use rule-based logic to select the appropriate tool or fallback to LLM."""
    try:
        # 🔍 Check if any tool should be used
        response = agent.run(user_input)

        if "No matching projects found" in response or response.strip() == "":
            # If no relevant tool output, use fallback LLM
            print("⚠️ No tool matched. Using fallback LLM.")
            response = fallback_llm.invoke(f"User asked: {user_input}. Provide a detailed response.")

        return response

    except Exception as e:
        print(f"❌ Error in tool execution: {str(e)}")
        # If the tool fails, always return a response from the fallback LLM
        return fallback_llm.invoke(f"User asked: {user_input}. Provide a detailed response.")

