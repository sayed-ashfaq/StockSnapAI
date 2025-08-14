import os
from pathlib import Path
import logger

logger.basicConfig(level= logger.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

projectname= "StockSnapAI"

list_of_files = [
    ".github/workflows/.gitkeep",
    f"src/{projectname}/__init__.py",
]