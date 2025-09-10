from dotenv import load_dotenv
import os
import requests
load_dotenv()

ENDPOINTS = "https://www.alphavantage.co/query"
STOCKAPI= os.getenv("ALPHAVANTAGE_API_KEY")

stockname= 'AAPL'

daily_param={
    'function': 'TIME_SERIES_DAILY',
    'symbol': stockname,
    'apikey': "FLQUQQVF67PWQ2EH",
}

response = requests.get(ENDPOINTS, params=daily_param)
print(response.json())
print(STOCKAPI)