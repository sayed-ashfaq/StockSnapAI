# StockSnap AI 📰📊

A AI-powered stock RAG app where users can:
- Enter a stock ticker or company name.
- Fetch and summarize the latest news.
- View key financial metrics.
- Chat with recent stock performance data.

---

## 🚀 Features
### Tab 1: News Chat
- Input: API key + Stock ticker/company name.
- Fetch top 3–5 recent headlines.
- AI-generated summaries with source links.
- Chat with the stock’s recent news data (RAG-powered).

### Tab 2: Analysis
- View key metrics: Price, % change, market cap, P/E ratio, etc.
- Quick access to KPIs from:
  - Profit & Loss
  - Cashflow
  - Balance Sheet

### Tab 3: Annual Report Chat (Future)
- Upload a company’s annual report (PDF).
- Get a summary and chat with its contents.

---

## 🛠 Tech Stack
- **Frontend:** Streamlit (or minimal React)
- **Backend:** Python (FastAPI optional for API handling)
- **Vector DB:** ChromaDB (local storage)
- **LLM:** OpenAI GPT / Gemini / Local LLaMA
- **Data Sources:**
  - News: Finnhub / Alpha Vantage / Yahoo Finance API
  - Financials: Alpha Vantage / Yahoo Finance

---

## 📂 Project Structure
```bash
project_root/
│
├── config/                         # Configuration files
│   └── config.yaml
│
├── notebooks/                      # Jupyter notebooks for experiments
│   └── experiments.ipynb
│
├── prompts/                        # Prompt templates & libraries
│   └── prompt_library.py
│
├── src/                            # Backend application logic
│   ├── annual_report_analysis/     # (future) Annual report parsing
│   ├── news_summarizer/            # Latest headlines & summaries
│   ├── stock_analyzer/             # Stock metrics & financial KPIs
│   │   ├── get_news.py
│   │   ├── summarizer.py
│   │   └── chat.py
│   └── utils/                      # Utility functions
│       └── utils.py
│
├── data/                           # Local data storage
│   ├── chroma_db/                  # ChromaDB vector store
│   └── temp/                       # Temporary downloaded files
│
├── app.py                          # Main app entry point (Streamlit/FastAPI)
├── config.py                       # API keys, constants, global settings
├── requirements.txt                # Python dependencies
├── template.py                     # Script template (utility or boilerplate)
├── test.py                         # Test scripts
└── README.md                       # Project documentation

```

# TODO:
1. Scrape the news content and store it in .txt file
2. ingest the text data into the vector database(Chroma/FAISS)
3. Model is not storing conversation history, find a way
### Module 2 
1. Getting KPIs from web using API and show it. like tickertape
2. 

