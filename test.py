import uuid
import os

docs= [
        "C:\\Users\\302sy\\Desktop\\Generative AI\\StockSnapAI\\data\\AI-Driven Market Rally August 2025.txt",
        "C:\\Users\\302sy\\Desktop\\Generative AI\\StockSnapAI\\data\\Stock Market Overview August 2025.txt",
        "C:\\Users\\302sy\\Desktop\\Generative AI\\StockSnapAI\\data\\Tariff Impacts on Markets August 20.txt"
    ]
path= "C:\\Users\\302sy\\Desktop\\Generative AI\\StockSnapAI\\notebooks"
for doc in docs:
    unique_name= f"{uuid.uuid4().hex[:8]}.txt"
    temp_path= os.path.join(path, unique_name)
    with open(path, "w", encoding= 'utf-8') as f:
        f.write(doc)