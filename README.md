
---

# 🤖 AI Finance Copilot (Prototype)

> ⚠️ **Prototype App** – This project is an experimental build to test and validate the idea of an AI-powered finance assistant.
> 🚀 A full **industry-grade web application** is planned for future development.

AI Finance Copilot is a **Streamlit-based prototype** that assists traders and analysts with **stock sentiment analysis** and **financial document insights**. It combines real-time market intelligence with AI-powered document analysis to demonstrate what a next-generation financial research tool could look like.

---

## ✨ Features

### 📈 Stock News & Sentiment Analysis

* Add multiple stocks to a custom portfolio
* Get **real-time news analysis** with AI sentiment scoring
* Portfolio-level insights: themes, risks, opportunities
* Individual stock summaries with sentiment impact
* Portfolio distribution charts (bullish, bearish, neutral)

### 📄 Document Chat & Analysis

* Upload financial documents (earnings, annual reports, etc.)
* AI-powered summaries with **red flag detection**
* Chat with documents using natural language (with citations)
* Quick questions for faster insights
* Export chat history

---
## 📊 Dashboard

#### Link: https://stocksnapai.streamlit.app/

## 🖼️ Screenshots

### Home & API Configuration

<img width="300" height="289" alt="Screenshot 2025-09-01 122910" src="https://github.com/user-attachments/assets/0be481f8-9bfb-41ce-82c8-46e0853f51ca" />

### Stock News & Portfolio Analysis

<img width="413" height="500" alt="StockSnapAI-1" src="https://github.com/user-attachments/assets/a9caefda-6a56-43ff-8667-50a012ae1e26" />

### Document Upload & Summaries

<img width="413" height="500" alt="StockSnapAI-2" src="https://github.com/user-attachments/assets/07943934-3755-4db3-b8b3-400279f31c31" />

### Interactive Document Q\&A

<img width="413" height="409" alt="StocksnapAI-3" src="https://github.com/user-attachments/assets/aba73a30-f0a4-4f41-adff-00320154b881" />


---

## 🚀 Getting Started

### 1. Clone Repository

```bash
git clone https://github.com/sayed-ashfaq/StockSnapAI
cd StockSnapAI
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. API Keys (Free Tiers Available)

* [OpenAI](https://platform.openai.com/api-keys) – embeddings & analysis
* [Google AI](https://makersuite.google.com/app/apikey) – Gemini model
* [Tavily](https://app.tavily.com/) – real-time news search

Enter keys in the **sidebar** after starting the app.

### 4. Run the App

```bash
streamlit run main.py
```

---

## 🛠️ Tech Stack

* **Streamlit** – Web interface
* **LangChain + LangGraph** – AI orchestration
* **OpenAI Embeddings** – Document vectorization
* **Google Gemini 2.0** – LLM for chat & analysis
* **Tavily Search** – Real-time financial news

---

## 📂 Project Structure

```
ai-finance-copilot/
├── main.py                 # Streamlit app entry point
├── requirements.txt        # Dependencies
└── modules/
    ├── stock_analyzer.py   # Stock sentiment logic
    └── document_chat.py    # Document RAG + Q&A
└──...
└──...
```

---

## ⚠️ Prototype Limitations

* Basic UI/UX
* No persistent data storage
* Limited error handling
* Session-based API key storage
* Charts & analytics are minimal

---

## 🔮 Roadmap (Industry-Grade Version)

Planned features for the full-scale application:

* Advanced dashboards & visualizations
* Persistent storage (DB-backed portfolio & documents)
* Real-time alerts & monitoring
* Multi-user support with authentication
* Enhanced security for sensitive documents
* Web based app
* Exception handing and custom logging
* Advanced vectorstore chunking, retriving methods

---

## 📞 Contact

For collaboration or updates on the full version:

* **Email**: [302syedashfaq@gmail.com](mailto:302syedashfaq@gmai.com)
* **LinkedIn**: [sayed-ashfaq](https://www.linkedin.com/in/sayed-ashfaq/)

---

⚖️ **Disclaimer**: This prototype is for demonstration purposes only. It does not provide financial advice.

⭐ Star the repo if you find this project interesting!

---

Would you like me to also **make a GitHub-ready version with actual Markdown formatting + screenshot placeholders replaced with your uploaded images** (renamed properly into a `/screenshots/` folder)? That way, you can just copy-paste it into your repo.
