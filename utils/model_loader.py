import os
import sys
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from openai.types import embedding_model
from utils.config_loader import load_config
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI


class ModelLoader:
    """
    An Utility class to load embedding and LLM models.
    """
    def __init__(self):
        load_dotenv()
        self._validate_env()
        self.config = load_config(config_path="..\\config\\config.yaml")
    def _validate_env(self):
        """
        Validate the environment variables.
        Ensure API key is set correctly.
        :return:
        """
        required_vars= ["GOOGLE_API_KEY", "OPENAI_API_KEY", "GROQ_API_KEY"]
        self.api_key = {key: os.getenv(key) for key in required_vars}
        missing= [k for k, v in self.api_key.items() if not v]
        if missing:
            raise EnvironmentError("Environment variables not set.")

    def load_embedding_model(self):
        """
        load and return the embedding model.
        :return:
        """
        model_name= self.config["embedding_model"]["model_name"]
        return GoogleGenerativeAIEmbeddings(model= model_name)

    def load_llm(self, model_name= "groq"):
        """Initiate and load the LLM model."""
        llm_block= self.config["llm"]


        if model_name in llm_block:
            llm_config=llm_block[model_name]
            provider= llm_config.get("provider")
            model_name = llm_config.get("model_name")
            temperature = llm_config.get("temperature")
            max_tokens = llm_config.get("max_tokens")
        else:
            raise EnvironmentError("Model not found")

        if provider == "groq":
            llm= ChatGroq(
                model= model_name,
                api_key= self.api_key["GROQ_API_KEY"],
                temperature= temperature,
            )
            return llm
        elif provider == "google":
            llm= ChatGoogleGenerativeAI(
                model= model_name,
                temperature= temperature,
                google_api_key= self.api_key["GOOGLE_API_KEY"],
            )
            return llm
        elif provider == "openai":
            llm= ChatOpenAI(
                model= model_name,
                api_key= self.api_key["OPENAI_API_KEY"],
            )
            return llm
        else:
            raise ValueError(f"Unknown provider: {provider}")



if __name__ == "__main__":
    loader= ModelLoader()

    # Test embeddings model
    embedding_model= loader.load_embedding_model()
    print(f"Embedding model loaded: {embedding_model}")

    # test the model loader
    result = embedding_model.embed_query("Hello World")
    print(f" Embedding Result{result}")

    # Test the LLm loading based on YAML config
    llm= loader.load_llm("openai")
    print(f"LMM model loaded: {llm}")

    # test the model loader
    result= llm.invoke("Hi, who made you")
    print(f" LLM Result{result.content}")