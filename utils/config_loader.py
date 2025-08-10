import yaml
from pathlib import Path


def load_config(config_path: str = "C:\\Users\\302sy\\Desktop\\Generative AI\\StockSnapAI\\utils\\config_loader.py") -> dict:
    with open(Path(config_path), "r") as file:
        config=yaml.safe_load(file)
    return config

if __name__ == "__main__":
    testing_config = load_config()
    print(testing_config)