import os
from pathlib import Path
import logging

logging.basicConfig(level= logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

projectname= "StockSnapAI"

list_of_files = [
    ".github/workflows/.gitkeep",
    f"src/{projectname}/__init__.py",
]