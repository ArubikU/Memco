import os
import json
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
import requests
from dotenv import load_dotenv

class EmbeddingProvider(ABC):
    """
    Abstract base class for embedding providers.
    """
    @abstractmethod
    def get_embedding(self, text: str) -> List[float]:
        """Get embedding for the given text."""
        pass
    
    @abstractmethod
    def get_batch_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings for a batch of texts."""
        pass


class OpenAIEmbedding(EmbeddingProvider):
    """
    OpenAI embedding provider.
    """
    def __init__(self, api_key: str, model: str = "text-embedding-3-small"):
        self.api_key = api_key
        self.model = model
        self.api_url = "https://api.openai.com/v1/embeddings"
    
    def get_embedding(self, text: str) -> List[float]:
        """Get embedding for the given text."""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        data = {
            "input": text,
            "model": self.model
        }
        
        response = requests.post(self.api_url, headers=headers, json=data)
        response.raise_for_status()
        
        result = response.json()
        return result["data"][0]["embedding"]
    
    def get_batch_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings for a batch of texts."""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        data = {
            "input": texts,
            "model": self.model
        }
        
        response = requests.post(self.api_url, headers=headers, json=data)
        response.raise_for_status()
        
        result = response.json()
        return [item["embedding"] for item in result["data"]]


class CohereEmbedding(EmbeddingProvider):
    """
    Cohere embedding provider.
    """
    def __init__(self, api_key: str, model: str = "embed-english-v3.0"):
        self.api_key = api_key
        self.model = model
        self.api_url = "https://api.cohere.com/v1/embed"

    def get_embedding(self, text: str) -> List[float]:
        """Get embedding for the given text."""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"BEARER {self.api_key}"
        }

        data = {
            "texts": [text],
            "model": self.model,
            "input_type": "classification",
            "truncate": "NONE"
        }

        response = requests.post(self.api_url, headers=headers, json=data)
        response.raise_for_status()

        result = response.json()
        return result["embeddings"][0]
    
    def get_batch_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings for a batch of texts."""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        data = {
            "texts": texts,
            "model": self.model
        }
        
        response = requests.post(self.api_url, headers=headers, json=data)
        response.raise_for_status()
        
        result = response.json()
        return result["embeddings"]


def get_embedding_provider() -> Optional[EmbeddingProvider]:
    """
    Get an embedding provider based on environment variables.
    Reads from .env file if available.
    """
    # Load environment variables from .env file
    load_dotenv()
    
    # Check for OpenAI configuration
    openai_api_key = os.getenv("OPENAI_API_KEY")
    openai_model = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
    
    if openai_api_key:
        return OpenAIEmbedding(openai_api_key, openai_model)
    
    # Check for Cohere configuration
    cohere_api_key = os.getenv("COHERE_API_KEY")
    cohere_model = os.getenv("COHERE_EMBEDDING_MODEL", "embed-english-v3.0")
    
    if cohere_api_key:
        return CohereEmbedding(cohere_api_key, cohere_model)
    
    # No provider available
    return None
