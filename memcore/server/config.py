import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv

class ServerConfig:
    """
    Configuration for the MemCore server.
    """
    def __init__(self, env_file: str = ".env"):
        # Load environment variables
        load_dotenv(env_file)
        
        # Server settings
        self.host = os.getenv("MEMCORE_HOST", "0.0.0.0")
        self.port = int(os.getenv("MEMCORE_PORT", "8000"))
        
        # MemCore settings
        self.mem_path = os.getenv("MEMCORE_PATH", ".memfolder")
        self.encryption_key = os.getenv("MEMCORE_ENCRYPTION_KEY")
        
        # Embedding settings
        self.embedding_provider = os.getenv("EMBEDDING_PROVIDER", "").lower()
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.openai_model = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
        self.cohere_api_key = os.getenv("COHERE_API_KEY")
        self.cohere_model = os.getenv("COHERE_EMBEDDING_MODEL", "embed-english-v3.0")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return {
            "server": {
                "host": self.host,
                "port": self.port
            },
            "memcore": {
                "mem_path": self.mem_path,
                "encryption_key": "***" if self.encryption_key else None
            },
            "embedding": {
                "provider": self.embedding_provider,
                "openai_model": self.openai_model if self.openai_api_key else None,
                "cohere_model": self.cohere_model if self.cohere_api_key else None
            }
        }
    
    def get_embedding_env(self) -> Dict[str, str]:
        """Get embedding environment variables."""
        env = {}
        
        if self.embedding_provider == "openai" and self.openai_api_key:
            env["OPENAI_API_KEY"] = self.openai_api_key
            env["OPENAI_EMBEDDING_MODEL"] = self.openai_model
        elif self.embedding_provider == "cohere" and self.cohere_api_key:
            env["COHERE_API_KEY"] = self.cohere_api_key
            env["COHERE_EMBEDDING_MODEL"] = self.cohere_model
        
        return env
