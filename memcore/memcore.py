import os
import json
import uuid
import time
import shutil
import datetime
import pickle
from typing import Dict, List, Any, Optional, Union, Callable
from pathlib import Path
import base64
import hashlib
from cryptography.fernet import Fernet
from .vector_search import VectorSearch
from .embedding import get_embedding_provider, EmbeddingProvider

class MemoryRecord:
    """
    Represents a single memory record in the MemCore system.
    """
    def __init__(self, 
                 id: str = None, 
                 content: str = "", 
                 tags: List[str] = None, 
                 metadata: Dict[str, Any] = None, 
                 importance: float = 0.5, 
                 created_at: float = None, 
                 updated_at: float = None, 
                 source: str = "", 
                 embedding: List[float] = None):
        self.id = id or str(uuid.uuid4())
        self.content = content
        self.tags = tags or []
        self.metadata = metadata or {}
        self.importance = importance
        self.created_at = created_at or time.time()
        self.updated_at = updated_at or self.created_at
        self.source = source
        self.embedding = embedding or []
    
    def to_dict(self, no_embedding: bool = False) -> Dict[str, Any]:
        """Convert the memory record to a dictionary."""
        if no_embedding:
            return {
                "id": self.id,
                "content": self.content,
                "tags": self.tags,
                "metadata": self.metadata,
                "importance": self.importance,
                "created_at": self.created_at,
                "updated_at": self.updated_at,
                "source": self.source
            }
        return {
            "id": self.id,
            "content": self.content,
            "tags": self.tags,
            "metadata": self.metadata,
            "importance": self.importance,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "source": self.source,
            "embedding": self.embedding
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MemoryRecord':
        """Create a memory record from a dictionary."""
        return cls(
            id=data.get("id"),
            content=data.get("content", ""),
            tags=data.get("tags", []),
            metadata=data.get("metadata", {}),
            importance=data.get("importance", 0.5),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
            source=data.get("source", ""),
            embedding=data.get("embedding", [])
        )


class MemoryBuilder:
    """
    Builder pattern for creating MemoryRecord objects.
    """
    def __init__(self, ai_provider: Optional['EmbeddingProvider'] = None):
        self.record = MemoryRecord()
        self.ai_provider = ai_provider
    
    def set_content(self, content: str) -> 'MemoryBuilder':
        """Set the content of the memory."""
        self.record.content = content
        # Generate embedding if AI provider is available
        if self.ai_provider and content:
            self.record.embedding = self.ai_provider.get_embedding(content)
        return self
    
    def set_tags(self, tags: Union[List[str], str]) -> 'MemoryBuilder':
        """Set the tags for the memory."""
        if isinstance(tags, str):
            tags = [tag.strip() for tag in tags.split(",")]
        self.record.tags = tags
        return self
    
    def set_metadata(self, metadata: Dict[str, Any]) -> 'MemoryBuilder':
        """Set the metadata for the memory."""
        self.record.metadata = metadata
        return self
    
    def set_importance(self, importance: float) -> 'MemoryBuilder':
        """Set the importance score for the memory."""
        self.record.importance = max(0.0, min(1.0, importance))
        return self
    
    def set_source(self, source: str) -> 'MemoryBuilder':
        """Set the source of the memory."""
        self.record.source = source
        return self
    
    def build(self) -> MemoryRecord:
        """Build and return the memory record."""
        
        if(not self.record.content and not self.record.embedding):
            raise ValueError("Memory must have either content or embedding")
        self.record.id = str(uuid.uuid4())
        self.record.created_at = time.time()
        
        return self.record


class MemTable:
    """
    Manages the memory table (index) for the MemCore system using a custom file-based approach.
    """
    def __init__(self, path: str):
        self.path = path
        self.index_file = os.path.join(path, "index.json")
        self.memories = {}
        self._load_index()
    
    def _load_index(self):
        """Load the index from disk."""
        if os.path.exists(self.index_file):
            try:
                with open(self.index_file, 'r') as f:
                    self.memories = json.load(f)
            except Exception as e:
                print(f"Error loading index: {e}")
                self.memories = {}
        else:
            self.memories = {}
    
    def _save_index(self):
        """Save the index to disk."""
        os.makedirs(os.path.dirname(self.index_file), exist_ok=True)
        with open(self.index_file, 'w') as f:
            json.dump(self.memories, f, indent=2)
    
    def add_memory(self, memory: MemoryRecord, encrypted: bool = False) -> str:
        """Add a memory record to the table."""
        memory_dict = memory.to_dict()
        memory_dict["encrypted"] = encrypted
        
        # Store in memory
        self.memories[memory.id] = memory_dict
        
        # Save to disk
        self._save_index()
        
        # Save the full memory to a .mem file
        mem_file = os.path.join(self.path, f"{memory.id}.mem")
        with open(mem_file, 'wb') as f:
            pickle.dump(memory_dict, f)
        
        return memory.id
    
    def get_memory(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """Get a memory record by ID."""
        if memory_id not in self.memories:
            return None
        
        # Load from .mem file for most up-to-date data
        mem_file = os.path.join(self.path, f"{memory_id}.mem")
        if os.path.exists(mem_file):
            try:
                with open(mem_file, 'rb') as f:
                    return pickle.load(f)
            except Exception as e:
                print(f"Error loading memory file: {e}")
                return self.memories.get(memory_id)
        
        return self.memories.get(memory_id)
    
    def update_memory(self, memory_id: str, fields: Dict[str, Any]) -> bool:
        """Update a memory record."""
        memory = self.get_memory(memory_id)
        if not memory:
            return False
        
        # Update fields
        for key, value in fields.items():
            if key in memory and key != "id":
                memory[key] = value
        
        # Update the updated_at timestamp
        memory["updated_at"] = time.time()
        
        # Update in memory
        self.memories[memory_id] = memory
        
        # Save to disk
        self._save_index()
        
        # Update the .mem file
        mem_file = os.path.join(self.path, f"{memory_id}.mem")
        with open(mem_file, 'wb') as f:
            pickle.dump(memory, f)
        
        return True
    
    def delete_memory(self, memory_id: str) -> bool:
        """Delete a memory record."""
        if memory_id not in self.memories:
            return False
        
        # Remove from memory
        del self.memories[memory_id]
        
        # Save to disk
        self._save_index()
        
        # Delete the .mem file
        mem_file = os.path.join(self.path, f"{memory_id}.mem")
        if os.path.exists(mem_file):
            os.remove(mem_file)
        
        return True
    
    def query(self, query_func: Callable[[Dict[str, Any]], bool]) -> List[Dict[str, Any]]:
        """Execute a query using a filter function."""
        results = []
        
        for memory_id, memory in self.memories.items():
            # Load from .mem file for most up-to-date data
            mem_file = os.path.join(self.path, f"{memory_id}.mem")
            if os.path.exists(mem_file):
                try:
                    with open(mem_file, 'rb') as f:
                        memory = pickle.load(f)
                except Exception:
                    pass  # Use the in-memory version if file can't be loaded
            
            if query_func(memory):
                results.append(memory)
        
        return results
    
    def close(self):
        """Close any open resources."""
        self._save_index()


class MemHistory:
    """
    Manages the history of memory changes using .memh files.
    """
    def __init__(self, path: str):
        self.path = path
        os.makedirs(path, exist_ok=True)
    
    def add_history(self, memory: MemoryRecord, action: str):
        """Add a history entry for a memory action."""
        history_path = os.path.join(self.path, memory.id)
        os.makedirs(history_path, exist_ok=True)
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        history_file = os.path.join(history_path, f"{timestamp}_{action}.memh")
        
        with open(history_file, 'wb') as f:
            pickle.dump(memory.to_dict(), f)
    
    def get_history(self, memory_id: str) -> List[Dict[str, Any]]:
        """Get the history of a memory record."""
        history_path = os.path.join(self.path, memory_id)
        if not os.path.exists(history_path):
            return []
        
        history = []
        for filename in sorted(os.listdir(history_path)):
            if filename.endswith('.memh'):
                file_path = os.path.join(history_path, filename)
                timestamp, action = filename.split('_', 1)
                action = action.replace('.memh', '')
                
                try:
                    with open(file_path, 'rb') as f:
                        data = pickle.load(f)
                    
                    history.append({
                        "timestamp": timestamp,
                        "action": action,
                        "data": data
                    })
                except Exception as e:
                    print(f"Error loading history file {file_path}: {e}")
        
        return history

class SearchResult:
    """
    Represents a search result.
    """
    def __init__(self, id: str, score: float, metadata: Dict[str, Any] = None):
        self.id = id
        self.score = score
        self.metadata = metadata or {}


class MemViewer:
    """
    Viewer for .mem files.
    """
    def __init__(self, path: str):
        self.path = path
    
    def list_memories(self) -> List[str]:
        """List all memory IDs."""
        memory_ids = []
        for filename in os.listdir(self.path):
            if filename.endswith('.mem'):
                memory_ids.append(filename.replace('.mem', ''))
        return memory_ids
    
    def view_memory(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """View a memory by ID."""
        mem_file = os.path.join(self.path, f"{memory_id}.mem")
        if not os.path.exists(mem_file):
            return None
        
        try:
            with open(mem_file, 'rb') as f:
                memory = pickle.load(f)
            return memory
        except Exception as e:
            print(f"Error loading memory file: {e}")
            return None
    
    def view_all_memories(self) -> List[Dict[str, Any]]:
        """View all memories."""
        memories = []
        for memory_id in self.list_memories():
            memory = self.view_memory(memory_id)
            if memory:
                memories.append(memory)
        return memories
    
    def search_memories(self, query: str) -> List[Dict[str, Any]]:
        """Search memories by content or tags."""
        query = query.lower()
        results = []
        
        for memory_id in self.list_memories():
            memory = self.view_memory(memory_id)
            if not memory:
                continue
            
            # Search in content
            if query in memory.get("content", "").lower():
                results.append(memory)
                continue
            
            # Search in tags
            for tag in memory.get("tags", []):
                if query in tag.lower():
                    results.append(memory)
                    break
        
        return results
    
    def export_memory(self, memory_id: str, output_path: str) -> bool:
        """Export a memory to a JSON file."""
        memory = self.view_memory(memory_id)
        if not memory:
            return False
        
        try:
            with open(output_path, 'w') as f:
                json.dump(memory, f, indent=2)
            return True
        except Exception as e:
            print(f"Error exporting memory: {e}")
            return False



class MemCore:
    """
    Core class for the memory management system.
    """
    def __init__(self, 
                 root_path: str = ".memfolder", 
                 encryption_key: Optional[str] = None,
                 embedding_provider: Optional[EmbeddingProvider] = None):
        self.root_path = os.path.abspath(root_path)
        self.encryption_key = self._setup_encryption(encryption_key)
        self.embedding_provider = embedding_provider or get_embedding_provider()
        
        # Create the folder structure
        self._setup_folders()
        
        # Initialize components
        self.table = MemTable(os.path.join(self.root_path, ".memtable"))
        self.history = MemHistory(os.path.join(self.root_path, ".memhistory"))
        self.vector_search = VectorSearch(os.path.join(self.root_path, ".memvectors"))
        self.viewer = MemViewer(os.path.join(self.root_path, ".memtable"))
    
    def _setup_encryption(self, key: Optional[str]) -> Optional[Fernet]:
        """Set up encryption with the provided key."""
        if not key:
            return None
        
        # Generate a 32-byte key from the provided key
        hashed_key = hashlib.sha256(key.encode()).digest()
        encoded_key = base64.urlsafe_b64encode(hashed_key)
        return Fernet(encoded_key)
    
    def _setup_folders(self):
        """Set up the folder structure for the memory system."""
        os.makedirs(self.root_path, exist_ok=True)
        os.makedirs(os.path.join(self.root_path, ".memtable"), exist_ok=True)
        os.makedirs(os.path.join(self.root_path, ".memhistory"), exist_ok=True)
        os.makedirs(os.path.join(self.root_path, ".memvectors"), exist_ok=True)
    
    def _encrypt_data(self, data):
        """Encrypt any data using the encryption key."""
        if not self.encryption_key:
            return data
        
        if isinstance(data, str):
            return self.encryption_key.encrypt(data.encode()).decode()
        elif isinstance(data, list):
            return [self._encrypt_data(item) for item in data]
        elif isinstance(data, dict):
            return {key: self._encrypt_data(value) for key, value in data.items()}
        else:
            # For other types, convert to string first
            return self._encrypt_data(str(data))
    
    def _decrypt_data(self, data):
        """Decrypt any data using the encryption key."""
        if not self.encryption_key:
            return data
        
        if isinstance(data, str):
            try:
                return self.encryption_key.decrypt(data.encode()).decode()
            except:
                # If decryption fails, return the original data
                return data
        elif isinstance(data, list):
            return [self._decrypt_data(item) for item in data]
        elif isinstance(data, dict):
            return {key: self._decrypt_data(value) for key, value in data.items()}
        else:
            return data
    def add_memory(self, memory: Union[MemoryRecord, Dict[str, Any]], encrypted: bool = False) -> str:
        """Add a memory record to the system."""
        if isinstance(memory, dict):
            memory = MemoryRecord.from_dict(memory)
        
        # Generate embedding if not already present
        if not memory.embedding and self.embedding_provider:
            memory.embedding = self.embedding_provider.get_embedding(memory.content)
        
        # Store original values for vector search
        original_content = memory.content
        original_tags = memory.tags.copy() if memory.tags else []
        
        # Encrypt fields if requested
        if encrypted and self.encryption_key:
            memory.content = self._encrypt_data(memory.content)
            memory.tags = self._encrypt_data(memory.tags)
            memory.source = self._encrypt_data(memory.source)
            memory.metadata = self._encrypt_data(memory.metadata)
        
        # Add to table
        memory_id = self.table.add_memory(memory, encrypted)
        
        # Add to history
        self.history.add_history(memory, "create")
        
        # Add to vector search if embedding exists
        if memory.embedding:
            self.vector_search.add_vector(memory_id, memory.embedding, {
                "content": original_content,
                "tags": original_tags,
                "importance": memory.importance
            })
        
        return memory_id
    
    def get_memory(self, memory_id: str) -> Optional[MemoryRecord]:
        """Get a memory record by ID."""
        data = self.table.get_memory(memory_id)
        if not data:
            return None
        
        # Decrypt fields if encrypted
        if data.get("encrypted", False) and self.encryption_key:
            data["content"] = self._decrypt_data(data["content"])
            data["tags"] = self._decrypt_data(data["tags"])
            data["source"] = self._decrypt_data(data["source"])
            data["metadata"] = self._decrypt_data(data["metadata"])
        
        return MemoryRecord.from_dict(data)
    
    def update_memory(self, memory_id: str, fields: Dict[str, Any]) -> bool:
        """Update a memory record."""
        memory = self.get_memory(memory_id)
        if not memory:
            return False
        
        # Get the original record data
        original_data = self.table.get_memory(memory_id)
        was_encrypted = original_data.get("encrypted", False)
        
        # Update fields
        for key, value in fields.items():
            if hasattr(memory, key) and key != "id":
                setattr(memory, key, value)
        
        # Update embedding if content changed and we have a provider
        content_changed = "content" in fields
        if content_changed and self.embedding_provider:
            memory.embedding = self.embedding_provider.get_embedding(memory.content)
        
        # Store original values for vector search
        original_content = memory.content
        original_tags = memory.tags.copy() if memory.tags else []
        
        # Encrypt fields if it was encrypted before
        if was_encrypted and self.encryption_key:
            memory.content = self._encrypt_data(memory.content)
            memory.tags = self._encrypt_data(memory.tags)
            memory.source = self._encrypt_data(memory.source)
            memory.metadata = self._encrypt_data(memory.metadata)
        
        # Update in table
        update_dict = {k: v for k, v in memory.to_dict().items() if k != "id"}
        success = self.table.update_memory(memory_id, update_dict)
        
        if success:
            # Add to history
            self.history.add_history(memory, "update")
            
            # Update vector search if embedding changed
            if memory.embedding and (content_changed or "embedding" in fields):
                self.vector_search.update_vector(memory_id, memory.embedding, {
                    "content": original_content,
                    "tags": original_tags,
                    "importance": memory.importance
                })
        
        return success
    
    def delete_memory(self, memory_id: str) -> bool:
        """Delete a memory record."""
        memory = self.get_memory(memory_id)
        if not memory:
            return False
        
        # Delete from table
        success = self.table.delete_memory(memory_id)
        
        if success:
            # Add to history
            self.history.add_history(memory, "delete")
            
            # Delete from vector search
            self.vector_search.delete_vector(memory_id)
        
        return success
    
    def get_history(self, memory_id: str) -> List[Dict[str, Any]]:
        """Get the history of a memory record."""
        return self.history.get_history(memory_id)
    
    def memql_query(self, query: str) -> List[MemoryRecord]:
        """Execute a MemQL query."""
        parser = MemQLParser(self)
        return parser.execute(query)
    
    def vector_search_query(self, text: str, top_k: int = 5) -> List[MemoryRecord]:
        """Search for memories similar to the given text."""
        if not self.embedding_provider:
            raise ValueError("No embedding provider available for vector search")
        
        # Generate embedding for the query text
        query_embedding = self.embedding_provider.get_embedding(text)
        
        # Search for similar vectors
        results = self.vector_search.search(query_embedding, top_k)
        
        # Fetch the full memory records
        memories = []
        for result in results:
            memory = self.get_memory(result.id)
            if memory:
                memories.append(memory)
        
        return memories
    
    def export_json(self, output_path: str) -> int:
        """Export all memories to a JSON file."""
        memories = self.viewer.view_all_memories()
        
        # Decrypt content if encrypted
        for memory in memories:
            if memory.get("encrypted", False) and self.encryption_key:
                memory["content"] = self._decrypt_data(memory["content"])
                memory["encrypted"] = False  # Mark as decrypted in the export
        
        with open(output_path, 'w') as f:
            json.dump(memories, f, indent=2)
        
        return len(memories)
    
    def import_json(self, input_path: str, encrypt: bool = False) -> int:
        """Import memories from a JSON file."""
        with open(input_path, 'r') as f:
            memories = json.load(f)
        
        count = 0
        for memory_data in memories:
            memory = MemoryRecord.from_dict(memory_data)
            self.add_memory(memory, encrypted=encrypt)
            count += 1
        
        return count
    
    def backup(self) -> str:
        """Create a complete backup of the memory system."""
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        backup_dir = f"memcore_backup_{timestamp}"
        
        # Create backup directory
        os.makedirs(backup_dir, exist_ok=True)
        
        # Copy all files
        shutil.copytree(self.root_path, os.path.join(backup_dir, os.path.basename(self.root_path)))
        
        return os.path.abspath(backup_dir)
    
    def restore(self, backup_path: str) -> bool:
        """Restore from a backup."""
        mem_folder = None
        for item in os.listdir(backup_path):
            if item.startswith(".mem") or item == ".memfolder":
                mem_folder = item
                break
        
        if not mem_folder:
            return False
        
        # Close current connections
        self.table.close()
        self.vector_search.close()
        
        # Remove current folder
        shutil.rmtree(self.root_path)
        
        # Copy backup
        shutil.copytree(os.path.join(backup_path, mem_folder), self.root_path)
        
        # Reinitialize components
        self.table = MemTable(os.path.join(self.root_path, ".memtable"))
        self.history = MemHistory(os.path.join(self.root_path, ".memhistory"))
        self.vector_search = VectorSearch(os.path.join(self.root_path, ".memvectors"))
        self.viewer = MemViewer(os.path.join(self.root_path, ".memtable"))
        
        return True
    
    def close(self):
        """Close all connections."""
        self.table.close()
        self.vector_search.close()


class MemQLParser:
    """
    Parser for the MemQL query language.
    """
    def __init__(self, memcore: MemCore):
        self.memcore = memcore
    
    def execute(self, query: str) -> List[MemoryRecord]:
        """Execute a MemQL query."""
        query = query.strip()
        
        # CREATE MEM query
        if query.upper().startswith("CREATE MEM"):
            return self._execute_create(query)
        
        # DELETE query
        if query.upper().startswith("DELETE"):
            return self._execute_delete(query)
        
        if query.upper().startswith("UPDATE"):
            return self._execute_update(query)
        
        # SELECT query (default)
        return self._execute_select(query)
    
    def _execute_create(self, query: str) -> List[MemoryRecord]:
        """Execute a CREATE MEM query."""
        # Extract parameters from the query
        params_str = query[query.find("(")+1:query.rfind(")")]
        params = {}
        
        # Parse parameters
        for param in params_str.split(","):
            if "=" in param:
                key, value = param.split("=", 1)
                key = key.strip()
                value = value.strip()
                
                # Remove quotes if present
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]
                
                # Convert to appropriate type
                if key == "importance":
                    value = float(value)
                elif key == "tags":
                    value = [tag.strip() for tag in value.split()]
                
                params[key] = value
        
        # Create memory builder
        builder = MemoryBuilder(self.memcore.embedding_provider)
        
        # Set parameters
        if "content" in params:
            builder.set_content(params["content"])
        if "tags" in params:
            builder.set_tags(params["tags"])
        if "importance" in params:
            builder.set_importance(params["importance"])
        if "source" in params:
            builder.set_source(params["source"])
        
        # Build and add memory
        memory = builder.build()
        memory_id = self.memcore.add_memory(memory)
        
        # Return the created memory
        return [self.memcore.get_memory(memory_id)]
    
    def _execute_delete(self, query: str) -> List[MemoryRecord]:
        """Execute a DELETE query."""
        # Extract WHERE clause
        
        # Support DELETE * (delete all memories)
        if query.strip().upper() == "DELETE *":
            # Get all memories
            memories = self._execute_select("SELECT LIMIT 0")
            deleted = []
            for memory in memories:
                if self.memcore.delete_memory(memory.id):
                    deleted.append(memory)
            return deleted
                    
        where_clause = query[query.upper().find("WHERE")+5:].strip()
        
        # Get memories that match the WHERE clause
        memories = self._execute_select(f"SELECT WHERE {where_clause}")
        
        # Delete each memory
        deleted = []
        for memory in memories:
            if self.memcore.delete_memory(memory.id):
                deleted.append(memory)
        
        return deleted
    
    def _execute_select(self, query: str) -> List[MemoryRecord]:
        """Execute a SELECT query."""
        # Default query
        if not query.upper().startswith("SELECT"):
            query = f"SELECT {query}"
        
        # Extract WHERE clause
        where_clause = ""
        if "WHERE" in query.upper():
            where_index = query.upper().find("WHERE")
            where_clause = query[where_index+5:]
            
            # Extract ORDER BY if present
            if "ORDER BY" in where_clause.upper():
                order_index = where_clause.upper().find("ORDER BY")
                where_clause = where_clause[:order_index].strip()
        
        # Extract ORDER BY clause
        order_by = ""
        order_desc = False
        if "ORDER BY" in query.upper():
            order_index = query.upper().find("ORDER BY")
            order_by = query[order_index+8:].strip()
            
            # Check for DESC
            if "DESC" in order_by.upper():
                order_desc = True
                order_by = order_by.upper().replace("DESC", "").strip()
        
        limit = 50
        if "LIMIT" in query.upper():
            limit_index = query.upper().find("LIMIT")
            limit = int(query[limit_index+5:].strip())
            
        vector_search = False
        vector_search_vector = None
        if "VECTOR" in query.upper():
            vector_search_index = query.upper().find("VECTOR")
            # Extract the query string after VECTOR (e.g., VECTOR 'Ai related')
            vector_search_query = query[vector_search_index + 6:].strip()
            # Remove quotes if present
            if vector_search_query.startswith("'") and vector_search_query.endswith("'"):
                vector_search_query = vector_search_query[1:-1]
            elif vector_search_query.startswith('"') and vector_search_query.endswith('"'):
                vector_search_query = vector_search_query[1:-1]
            vector_search = True
            vector_search_vector = self.memcore.embedding_provider.get_embedding(vector_search_query)
        vector_score = 0.5
        if "SCORE" in query.upper():
            vector_score_index = query.upper().find("SCORE")
            vector_score = float(query[vector_score_index + 6:].strip())
        # Define a filter function based on the WHERE clause
        def filter_func(memory):
            if vector_search:
                # Calculate similarity score
                vector_mem = memory['embedding']
                if not vector_mem:
                    return False
                score = self.memcore.vector_search._cosine_similarity(vector_mem, vector_search_vector)
                memory["similarity_score"] = score
                return score > vector_score
            
            if not where_clause:
                return True
            
            # Handle tag searches
            if "tags" in where_clause:
                if "=" in where_clause:
                    tag_value = where_clause.split("=")[1].strip()
                    if tag_value.startswith('"') and tag_value.endswith('"'):
                        tag_value = tag_value[1:-1]
                    return any(tag_value.lower() in tag.lower() for tag in memory.get("tags", []))
            if "encrypted" in where_clause:
                if "=" in where_clause:
                    encrypted_value = where_clause.split("=")[1].strip()
                    if encrypted_value.startswith('"') and encrypted_value.endswith('"'):
                        encrypted_value = encrypted_value[1:-1]
                    return memory.get("encrypted", False) == (encrypted_value.lower() == "true")
            # Handle content searches
            if "content" in where_clause:
                if "=" in where_clause:
                    content_value = where_clause.split("=")[1].strip()
                    if content_value.startswith('"') and content_value.endswith('"'):
                        content_value = content_value[1:-1]
                    return content_value.lower() in memory.get("content", "").lower()
            if "id" in where_clause:
                if "=" in where_clause:
                    id_value = where_clause.split("=")[1].strip()
                    if id_value.startswith('"') and id_value.endswith('"'):
                        id_value = id_value[1:-1]
                    return memory.get("id", "").lower() == id_value.lower()
            # Handle importance comparisons
            if "importance" in where_clause:
                importance = memory.get("importance", 0)
                if ">=" in where_clause:
                    importance_value = float(where_clause.split(">=")[1].strip())
                    return importance >= importance_value
                elif "<=" in where_clause:
                    importance_value = float(where_clause.split("<=")[1].strip())
                    return importance <= importance_value
                elif ">" in where_clause:
                    importance_value = float(where_clause.split(">")[1].strip())
                    return importance > importance_value
                elif "<" in where_clause:
                    importance_value = float(where_clause.split("<")[1].strip())
                    return importance < importance_value
            if "created_at" in where_clause:
                created_at = memory.get("created_at", 0)
                if ">=" in where_clause:
                    created_at_value = float(where_clause.split(">=")[1].strip())
                    return created_at >= created_at_value
                elif "<=" in where_clause:
                    created_at_value = float(where_clause.split("<=")[1].strip())
                    return created_at <= created_at_value
                elif ">" in where_clause:
                    created_at_value = float(where_clause.split(">")[1].strip())
                    return created_at > created_at_value
                elif "<" in where_clause:
                    created_at_value = float(where_clause.split("<")[1].strip())
                    return created_at < created_at_value
            if "updated_at" in where_clause:
                updated_at = memory.get("updated_at", 0)
                if ">=" in where_clause:
                    updated_at_value = float(where_clause.split(">=")[1].strip())
                    return updated_at >= updated_at_value
                elif "<=" in where_clause:
                    updated_at_value = float(where_clause.split("<=")[1].strip())
                    return updated_at <= updated_at_value
                elif ">" in where_clause:
                    updated_at_value = float(where_clause.split(">")[1].strip())
                    return updated_at > updated_at_value
                elif "<" in where_clause:
                    updated_at_value = float(where_clause.split("<")[1].strip())
                    return updated_at < updated_at_value
            if "source" in where_clause:
                if "=" in where_clause:
                    source_value = where_clause.split("=")[1].strip()
                    if source_value.startswith('"') and source_value.endswith('"'):
                        source_value = source_value[1:-1]
                    return source_value.lower() in memory.get("source", "").lower()
            # Default - pass through the clause
            return True
        
        # Execute query
        results = self.memcore.table.query(filter_func)
        
        # Sort results if ORDER BY is specified
        if order_by:
            if order_by.lower() == "importance":
                results.sort(key=lambda x: x.get("importance", 0), reverse=order_desc)
            elif order_by.lower() == "created_at":
                results.sort(key=lambda x: x.get("created_at", 0), reverse=order_desc)
            elif order_by.lower() == "updated_at":
                results.sort(key=lambda x: x.get("updated_at", 0), reverse=order_desc)
            elif order_by.lower() == "similarity_score":
                results.sort(key=lambda x: x.get("similarity_score", 0), reverse=order_desc)
        
        # Convert to MemoryRecord objects
        memories = []
        for result in results:
            # Decrypt content if encrypted
            if result.get("encrypted", False) and self.memcore.encryption_key:
                result["content"] = self.memcore._decrypt_data(result["content"])
            
            memories.append(MemoryRecord.from_dict(result))
    
        #aply limit
        if limit > 0:
            memories = memories[:limit]
        return memories

    def _execute_update(self, query: str) -> List[MemoryRecord]:
        """
        Execute an UPDATE query.
        Example: UPDATE SET content="new content", importance=0.9 WHERE id="abc"
        """
        # Extract SET and WHERE clauses
        set_clause = ""
        where_clause = ""
        if "SET" in query.upper():
            set_index = query.upper().find("SET")
            if "WHERE" in query.upper():
                    where_index = query.upper().find("WHERE")
                set_clause = query[set_index + 3:where_index].strip()
                where_clause = query[where_index + 5:].strip()
            else:
                    set_clause = query[set_index + 3:].strip()

        # Parse fields to update
        fields = {}
        for part in set_clause.split(","):
            if "=" in part:
                    key, value = part.split("=", 1)
                key = key.strip()
                value = value.strip()
                if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                elif value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]
                if key == "importance":
                        value = float(value)
                elif key == "tags":
                        value = [tag.strip() for tag in value.split()]
                fields[key] = value

        # Get memories that match the WHERE clause
        memories = self._execute_select(f"SELECT WHERE {where_clause}" if where_clause else "SELECT")
        updated = []
        for memory in memories:
            if self.memcore.update_memory(memory.id, fields):
                updated_mem = self.memcore.get_memory(memory.id)
                if updated_mem:
                    updated.append(updated_mem)
        return updated
                    # Convenience functions for direct use

def create_mem_folder(path: str = ".memfolder") -> bool:
    """Create a memory folder at the specified path."""
    try:
        os.makedirs(path, exist_ok=True)
        os.makedirs(os.path.join(path, ".memtable"), exist_ok=True)
        os.makedirs(os.path.join(path, ".memhistory"), exist_ok=True)
        os.makedirs(os.path.join(path, ".memvectors"), exist_ok=True)
        return True
    except Exception:
        return False

def add_memory(memory: Union[MemoryRecord, Dict[str, Any]], encrypted: bool = False, path: str = ".memfolder", encryption_key: Optional[str] = None) -> str:
    """Add a memory to the memory system."""
    memcore = MemCore(path, encryption_key)
    return memcore.add_memory(memory, encrypted)

def memql_query(query: str, path: str = ".memfolder", encryption_key: Optional[str] = None) -> List[MemoryRecord]:
    """Execute a MemQL query."""
    memcore = MemCore(path, encryption_key)
    return memcore.memql_query(query)

def update_memory(memory_id: str, fields: Dict[str, Any], path: str = ".memfolder", encryption_key: Optional[str] = None) -> bool:
    """Update a memory in the memory system."""
    memcore = MemCore(path, encryption_key)
    return memcore.update_memory(memory_id, fields)

def export_json(output_path: str, mem_path: str = ".memfolder", encryption_key: Optional[str] = None) -> int:
    """Export memories to a JSON file."""
    memcore = MemCore(mem_path, encryption_key)
    return memcore.export_json(output_path)

def import_json(input_path: str, mem_path: str = ".memfolder", encryption_key: Optional[str] = None, encrypt: bool = False) -> int:
    """Import memories from a JSON file."""
    memcore = MemCore(mem_path, encryption_key)
    return memcore.import_json(input_path, encrypt)
