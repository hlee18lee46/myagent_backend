from langchain.agents import initialize_agent, AgentType
from langchain.tools import Tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chat_models import ChatOpenAI

from dotenv import load_dotenv
import sys
import os
#from langchain.llms import HuggingFacePipeline
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
# Add the parent directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
# Now import the tool
from tools.github_search_tool import (
    search_github_projects_by_name,
    search_github_projects_by_frontend,
    search_github_projects_by_backend
)


# Load Google Gemini API Key
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


# Initialize the Gemini LLM
llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-pro",  # Updated model name
    google_api_key=GEMINI_API_KEY,
    #max_output_token=1024
)

"""
# ✅ Initialize OpenAI LLM with GPT-3.5-Turbo (Low-Cost Model)
llm = ChatOpenAI(
    model_name="gpt-3.5-turbo",  # ✅ Cost-effective model
    openai_api_key=OPENAI_API_KEY,
    temperature=0.7,  # Adjust for creativity (0.0 = more factual, 1.0 = more creative)
    max_tokens=4096
)
"""
"""
Hugging Face

# Load Hugging Face Token
HF_TOKEN = os.getenv("HUGGINGFACE_TOKEN")  # Store it in .env



# Load Mistral 7B model
model_name = "mistralai/Mistral-7B-v0.1"

tokenizer = AutoTokenizer.from_pretrained(
    model_name, 
    token=HF_TOKEN,
    truncation = True  # Authenticate the request
)

model = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype="auto",
    device_map="auto",
    token=HF_TOKEN
)
# Set pad_token_id explicitly to avoid warnings
model.config.pad_token_id = model.config.eos_token_id

# Create text-generation pipeline
text_gen_pipeline = pipeline(
    "text-generation",
    model=model,
    tokenizer=tokenizer,
    max_length=2048,
    do_sample=True,  # Enable sampling (fixes warning)
    temperature=0.7,  # Keep it only if `do_sample=True`
    top_p=0.95,  # Keep it only if `do_sample=True`
    repetition_penalty=1.1
)

# Initialize Mistral 7B as LangChain LLM
llm = HuggingFacePipeline(pipeline=text_gen_pipeline)

"""

# Define the tools the agent can use
tools = [
    Tool(
        name="GitHub Search by name",
        func=search_github_projects_by_name,
        description="Search GitHub projects stored in MongoDB with the name, only invoke this tool when asked to show details about a project, and provide the name, description, features, github, demo link, devpost."
    ),
    Tool(
        name="GitHub Search by Frontend",
        func=search_github_projects_by_frontend,
        description="Search GitHub projects stored in MongoDB that use a specific frontend technology, and provide the name, description, features, github, demo link, devpost."
    ),
    Tool(
        name="GitHub Search by Backend",
        func=search_github_projects_by_backend,
        description="Search GitHub projects stored in MongoDB that use a specific backend technology, and provide the name, description, features, github, demo link, devpost."
    )
]

# Create the tool-calling agent
agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True
)

