


## -----------------------Testing Chat_module-----------------------##

from src.news_summarizer.chat_module import ConversationalRAG
from src.news_summarizer.data_ingestion import NewsIngestor

docs= [
        "C:\\Users\\302sy\\Desktop\\Generative AI\\StockSnapAI\\data\\AI-Driven Market Rally August 2025.txt",
        "C:\\Users\\302sy\\Desktop\\Generative AI\\StockSnapAI\\data\\Stock Market Overview August 2025.txt",
        "C:\\Users\\302sy\\Desktop\\Generative AI\\StockSnapAI\\data\\Tariff Impacts on Markets August 20.txt"
    ]

# def test_conversationalRAG():
#     ingestor = NewsIngestor().ingest_files(docs)
#     rag= ConversationalRAG(retriever=ingestor, session_id="testing234")
#     question= input("user:")
#     while question not in ('q','quit', "exit"):
#         response= rag.invoke(question)
#         print(response)

if __name__ == "__main__":
    ingestor = NewsIngestor().ingest_files(docs)
    rag = ConversationalRAG(retriever=ingestor, session_id="testing234")
    question= "Your name is Stocker, summarize news for me"
    while question not in ('q', 'quit', "exit"):
        question = input("user:")
        response = rag.invoke(question)
        print(response)