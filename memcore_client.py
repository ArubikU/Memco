#!/usr/bin/env python3
import os
import json
import requests
from typing import List, Dict, Any, Optional, Tuple, Union
from dotenv import load_dotenv

class MemoryRecord:
    """
    Represents a memory record in the MemCore system.
    """
    def __init__(
        self,
        id: str = "",
        content: str = "",
        tags: List[str] = None,
        metadata: Dict[str, Any] = None,
        importance: float = 0.5,
        created_at: float = 0.0,
        updated_at: float = 0.0,
        source: str = "",
        embedding: List[float] = None
    ):
        self.id = id
        self.content = content
        self.tags = tags or []
        self.metadata = metadata or {}
        self.importance = importance
        self.created_at = created_at
        self.updated_at = updated_at
        self.source = source
        self.embedding = embedding or []
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MemoryRecord':
        """Create a MemoryRecord from a dictionary."""
        return cls(
            id=data.get('id', ''),
            content=data.get('content', ''),
            tags=data.get('tags', []),
            metadata=data.get('metadata', {}),
            importance=data.get('importance', 0.5),
            created_at=data.get('created_at', 0.0),
            updated_at=data.get('updated_at', 0.0),
            source=data.get('source', ''),
            embedding=data.get('embedding', [])
        )
    
    def to_dict(self, no_embedding: bool = False) -> Dict[str, Any]:
        """Convert to dictionary."""
        if no_embedding:
            return {
                'id': self.id,
                'content': self.content,
                'tags': self.tags,
                'metadata': self.metadata,
                'importance': self.importance,
                'created_at': self.created_at,
                'updated_at': self.updated_at,
                'source': self.source
            }
        return {
            'id': self.id,
            'content': self.content,
            'tags': self.tags,
            'metadata': self.metadata,
            'importance': self.importance,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'source': self.source,
            'embedding': self.embedding
        }

class MemCoreClient:
    """
    Client for interacting with the MemCore API.
    """
    def __init__(self, base_url: str, api_key: str = None):
        """
        Initialize the MemCore client.
        
        Args:
            base_url: Base URL of the MemCore API
            api_key: API key for authentication (optional, can be loaded from environment)
        """
        self.base_url = base_url.rstrip('/')
        
        # If no API key provided, try to load from environment
        if api_key is None:
            # Load .env file if it exists
            load_dotenv()
            api_key = os.getenv('MEMCORE_API_KEY', '')
        
        self.api_key = api_key
        self.session = requests.Session()
        
        # Set default headers
        if self.api_key:
            self.session.headers.update({'X-API-Key': self.api_key})
        else:
            self.session.headers.update({'X-API-Key': 'no-key'})
    
    def _request(self, method: str, path: str, data: Any = None) -> Any:
        """
        Make a request to the MemCore API.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            path: API path
            data: Request data (will be JSON-encoded)
            
        Returns:
            Response data (JSON-decoded)
            
        Raises:
            Exception: If the request fails
        """
        url = f"{self.base_url}{path}"
        headers = {'Content-Type': 'application/json'}
        
        response = self.session.request(
            method=method,
            url=url,
            headers=headers,
            json=data
        )
        
        # Check for errors
        if not response.ok:
            try:
                error_data = response.json()
                error_message = error_data.get('error', 'Unknown error')
            except:
                error_message = response.text
            
            raise Exception(f"API error ({response.status_code}): {error_message}")
        
        # Return response data
        if response.content:
            return response.json()
        return None
    
    def add_memory(
        self, 
        content: str, 
        tags: List[str] = None, 
        metadata: Dict[str, Any] = None, 
        importance: float = 0.5, 
        source: str = "", 
        encrypted: bool = False
    ) -> MemoryRecord:
        """
        Add a new memory.
        
        Args:
            content: Memory content
            tags: List of tags
            metadata: Additional metadata
            importance: Importance score (0.0-1.0)
            source: Source of the memory
            encrypted: Whether to encrypt the memory
            
        Returns:
            The created memory record
        """
        data = {
            'content': content,
            'tags': tags or [],
            'metadata': metadata or {},
            'importance': importance,
            'source': source,
            'encrypted': encrypted
        }
        
        response = self._request('POST', '/memories', data)
        return MemoryRecord.from_dict(response)
    
    def get_memory(self, memory_id: str) -> MemoryRecord:
        """
        Get a memory by ID.
        
        Args:
            memory_id: Memory ID
            
        Returns:
            The memory record
        """
        response = self._request('GET', f'/memories/{memory_id}')
        return MemoryRecord.from_dict(response)
    
    def update_memory(self, memory_id: str, updates: Dict[str, Any]) -> MemoryRecord:
        """
        Update a memory.
        
        Args:
            memory_id: Memory ID
            updates: Fields to update
            
        Returns:
            The updated memory record
        """
        response = self._request('PUT', f'/memories/{memory_id}', updates)
        return MemoryRecord.from_dict(response)
    
    def delete_memory(self, memory_id: str) -> bool:
        """
        Delete a memory.
        
        Args:
            memory_id: Memory ID
            
        Returns:
            True if successful
        """
        self._request('DELETE', f'/memories/{memory_id}')
        return True
    
    def vector_search(self, text: str, top_k: int = 5) -> List[MemoryRecord]:
        """
        Search for memories similar to the given text.
        
        Args:
            text: Query text
            top_k: Number of results to return
            
        Returns:
            List of memory records
        """
        data = {
            'text': text,
            'top_k': top_k
        }
        
        response = self._request('POST', '/query/vector', data)
        return [MemoryRecord.from_dict(item) for item in response]
    
    def memql_query(self, query: str) -> List[MemoryRecord]:
        """
        Execute a MemQL query.
        
        Args:
            query: MemQL query string
            
        Returns:
            List of memory records
        """
        data = {
            'query': query
        }
        
        response = self._request('POST', '/query/memql', data)
        return [MemoryRecord.from_dict(item) for item in response]
    
    def batch_add_memories(
        self, 
        memories: List[Union[Dict[str, Any], MemoryRecord]], 
        encrypted: bool = False
    ) -> Tuple[int, List[str]]:
        """
        Add multiple memories at once.
        
        Args:
            memories: List of memories (as dictionaries or MemoryRecord objects)
            encrypted: Whether to encrypt the memories
            
        Returns:
            Tuple of (number of successfully added memories, list of memory IDs)
        """
        # Convert MemoryRecord objects to dictionaries
        memory_dicts = []
        for memory in memories:
            if isinstance(memory, MemoryRecord):
                memory_dicts.append(memory.to_dict())
            else:
                memory_dicts.append(memory)
        
        data = {
            'memories': memory_dicts,
            'encrypted': encrypted
        }
        
        response = self._request('POST', '/batch/add', data)
        return response['count'], response['ids']
    
    def batch_update_memories(
        self, 
        updates: List[Tuple[str, Dict[str, Any]]]
    ) -> Tuple[int, List[str]]:
        """
        Update multiple memories at once.
        
        Args:
            updates: List of tuples (memory_id, update_dict)
            
        Returns:
            Tuple of (number of successfully updated memories, list of updated memory IDs)
        """
        data = {
            'updates': [
                {'id': memory_id, 'fields': update_dict}
                for memory_id, update_dict in updates
            ]
        }
        
        response = self._request('POST', '/batch/update', data)
        return response['count'], response['ids']
    
    def batch_delete_memories(self, memory_ids: List[str]) -> Tuple[int, List[str]]:
        """
        Delete multiple memories at once.
        
        Args:
            memory_ids: List of memory IDs to delete
            
        Returns:
            Tuple of (number of successfully deleted memories, list of deleted memory IDs)
        """
        data = {
            'ids': memory_ids
        }
        
        response = self._request('POST', '/batch/delete', data)
        return response['count'], response['ids']
    
    def export_memories(self, output_path: str) -> int:
        """
        Export memories to a JSON file.
        
        Args:
            output_path: Path to output file
            
        Returns:
            Number of exported memories
        """
        data = {
            'path': output_path
        }
        
        response = self._request('POST', '/export', data)
        return response['count']
    
    def import_memories(self, input_path: str, encrypt: bool = False) -> int:
        """
        Import memories from a JSON file.
        
        Args:
            input_path: Path to input file
            encrypt: Whether to encrypt the imported memories
            
        Returns:
            Number of imported memories
        """
        data = {
            'path': input_path,
            'encrypt': encrypt
        }
        
        response = self._request('POST', '/import', data)
        return response['count']
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get system statistics.
        
        Returns:
            Statistics dictionary
        """
        return self._request('GET', '/stats')

if __name__ == "__main__":
    # Example usage
    client = MemCoreClient("http://localhost:8000")
    
    # Add a memory
    memory = client.add_memory(
        content="This is a test memory",
        tags=["test", "example"],
        importance=0.8,
        source="example.py"
    )
    
    print(f"Added memory with ID: {memory.id}")
    
    # Get the memory
    retrieved = client.get_memory(memory.id)
    print(f"Retrieved memory: {retrieved.content}")
    
    # Update the memory
    updated = client.update_memory(memory.id, {"importance": 0.9})
    print(f"Updated memory importance: {updated.importance}")
    
    # Search for similar memories
    similar = client.vector_search("test memory")
    print(f"Found {len(similar)} similar memories")
    
    # Execute a MemQL query
    results = client.memql_query("SELECT WHERE tags == \"test\" ORDER BY importance DESC")
    print(f"Query returned {len(results)} memories")
    
    # Delete the memory
    client.delete_memory(memory.id)
    print("Memory deleted")
