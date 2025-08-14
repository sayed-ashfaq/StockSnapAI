import uuid
from pathlib import Path
import sys
from datetime import datetime
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from log_utils.custom_logging import CustomLogger
from exception.custom_exeption import CustomException
from utils.model_loader import ModelLoader

class NewsIngestor:
    def __init__(self, temp_dir: str = "data/new_ingestor", faiss_dir: str= "faiss_index"):
        try:
            self.log = CustomLogger().get_logger(__name__)

            # base dirs
            self.temp_dir = Path(temp_dir)
            self.faiss_dir = Path(faiss_dir)
            self.temp_dir.mkdir(parents=True, exist_ok=True)
            self.faiss_dir.mkdir(parents=True, exist_ok=True)

            # # sessionzed_path (Future)
            # self.session_id = session_id or f"session_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}"
            # self.session_temp_dir = self.temp_dir / self.session_id
            # self.session_faiss_dir = self.faiss_dir / self.session_id
            # self.session_temp_dir.mkdir(parents=True, exist_ok=True)
            # self.session_faiss_dir.mkdir(parents=True, exist_ok=True)

            self.model_loader = ModelLoader()

            self.log.info(
                "Document Ingestion initiated",
                temp_base= str(self.temp_dir),
                faiss_dir= str(self.faiss_dir),
                # Add sessions
            )
        except Exception as e:
            self.log.error("Failed to initialize NewsIngestor", error=str(e))
            raise CustomException("Failed to initialize NewsIngestor", sys)

    # def ingest_files(self, text_files):
    #     try:
    #         text_data= []
    #
    #         for file in text_files:
    #             # ext = Path(file).suffix.lower()
    #             # if ext != ".txt":
    #             #     self.log.warning("Unsupported file extension", filename= file.name)
    #
    #             unique_para_name= f"{uuid.uuid4().hex[:8]}.txt"
    #             temp_path = self.temp_dir/unique_para_name
    #
    #             with open(temp_path, "wb") as f:
    #                 f.write(file)
    #             self.log.info("File saved for ingestion", filename= file.name, saved_as= str(temp_path))
    #
    #             loader= TextLoader(str(temp_path), encoding="utf-8")
    #             docs= loader.load()
    #             text_data.append(docs)
    #         if not text_data:
    #             raise CustomException("No file data found", sys)
    #
    #         self.log.info(f"Paragraph has been loaded" )
    #         return self._create_retriever(text_data)
    #
    #     except Exception as e:
    #         self.log.error("Failed to ingest files to vector-database", error=str(e))

    def ingest_files(self, text_files):
        try:
            text_data = []

            for file_path in text_files:
                unique_para_name = f"{uuid.uuid4().hex[:8]}.txt"
                temp_path = self.temp_dir / unique_para_name

                with open(file_path, "rb") as source_file:
                    content = source_file.read()

                with open(temp_path, "wb") as f:
                    f.write(content)

                self.log.info(
                    "File saved for ingestion",
                    filename=file_path,
                    saved_as=str(temp_path)
                )

                loader = TextLoader(str(temp_path), encoding="utf-8")
                docs = loader.load()
                text_data.extend(docs)

            if not text_data:
                raise CustomException("No file data found", sys)

            self.log.info("Paragraph has been loaded")
            return self._create_retriever(text_data)

        except Exception as e:
            self.log.error("Failed to ingest files to vector-database", error=str(e))

    def _create_retriever(self, documents):
        try:
            splitter= RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)

            chunks= splitter.split_documents(documents)

            self.log.info(f"Documents split into chunks", total_chunks= len(chunks),)

            embeddings= self.model_loader.load_embedding_model()

            vector_store= FAISS.from_documents(chunks, embeddings)

            vector_store.save_local(str(self.faiss_dir))
            self.log.info("FAISS index saved to disk", path= str(self.faiss_dir))

            retriever= vector_store.as_retriever(search_type= "similarity", search_kwargs= {"k": 5})
            self.log.info("Retriever has been created and ready to use")

            return retriever
        except Exception as e:
            self.log.error("Failed to create retriever", error=str(e))
            raise CustomException("Failed to create retriever", sys)

## Testing retriever

if __name__ == "__main__":
    docs= [
        "C:\\Users\\302sy\\Desktop\\Generative AI\\StockSnapAI\\data\\AI-Driven Market Rally August 2025.txt",
        "C:\\Users\\302sy\\Desktop\\Generative AI\\StockSnapAI\\data\\Stock Market Overview August 2025.txt",
        "C:\\Users\\302sy\\Desktop\\Generative AI\\StockSnapAI\\data\\Tariff Impacts on Markets August 20.txt"
    ]
    retriever= NewsIngestor().ingest_files(docs)
    answer= retriever.invoke("What about ai")
    print("Response: ", answer)
