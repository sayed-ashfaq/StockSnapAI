import importlib.metadata

packages = [
    "python-dotenv",
    "python-multipart",
    "pypdf",
    "chardet",
    "charset-normalizer",
    "anthropic",
    "fastapi",
    "langchain",
    "langchain_chroma",
    "langchain_community",
    "langchain_core",
    "langchain_google_genai",
    "langchain_groq",
    "langchain_openai",
    "langchain_tavily",
    "langchain_text_splitters",
    "langgraph",
    "pandas",
    "Pillow",
    "pydantic",
    "pydantic_settings",
    "pymupdf",
    "PyPDF2",
    "pytest",
    "python_docx",
    "PyYAML",
    "Requests",
    "setuptools",
    "streamlit",
    "structlog",
    "supabase",
    "uvicorn"
]


for package in packages:
    try:
        version= importlib.metadata.version(package)
        print(f"{package}=={version}")
    except importlib.metadata.PackageNotFoundError:
        print(f"{package} (Not installed)")