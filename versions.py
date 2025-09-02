import importlib.metadata

packages= [
    "streamlit",
    "langchain",
    "langchain-openai",
    "langchain-google-genai",
    "langchain-groq",
    "langchain-tavily",
    "langchain-community",
    "langgraph",
    "python-dotenv",
    "pandas",
    "pypdf",
    "faiss-cpu",
    "structlog",
    "chardet",
    "charset-normalizer",
    "fastapi"
]

for package in packages:
    try:
        version= importlib.metadata.version(package)
        print(f"{package}=={version}")
    except importlib.metadata.PackageNotFoundError:
        print(f"{package} (Not installed)")