import os
import json
import csv
import time
from typing import List, Dict, Any, Optional, Union, Tuple, Iterator
from pathlib import Path
import sqlite3

from .memcore import MemCore, MemoryRecord, MemoryBuilder

class BatchProcessor:
    """
    Handles batch operations for the MemCore system.
    """
    def __init__(self, memcore: MemCore):
        self.memcore = memcore
    
    def batch_add(self, memories: List[Union[Dict[str, Any], MemoryRecord]], 
                  encrypted: bool = False) -> Tuple[int, List[str]]:
        """
        Add multiple memories at once.
        
        Args:
            memories: List of memories to add (as dictionaries or MemoryRecord objects)
            encrypted: Whether to encrypt the memories
            
        Returns:
            Tuple of (number of successfully added memories, list of memory IDs)
        """
        success_count = 0
        memory_ids = []
        
        # Start a transaction
        self.memcore.table.conn.execute("BEGIN TRANSACTION")
        
        try:
            for memory in memories:
                if isinstance(memory, dict):
                    # Convert dict to MemoryRecord
                    record = MemoryRecord.from_dict(memory)
                else:
                    record = memory
                
                # Generate embedding if not present and provider available
                if not record.embedding and self.memcore.embedding_provider:
                    record.embedding = self.memcore.embedding_provider.get_embedding(record.content)
                
                # Add memory
                memory_id = self.memcore.add_memory(record, encrypted=encrypted)
                memory_ids.append(memory_id)
                success_count += 1
            
            # Commit transaction
            self.memcore.table.conn.execute("COMMIT")
        except Exception as e:
            # Rollback on error
            self.memcore.table.conn.execute("ROLLBACK")
            raise e
        
        return success_count, memory_ids
    
    def batch_update(self, updates: List[Tuple[str, Dict[str, Any]]]) -> Tuple[int, List[str]]:
        """
        Update multiple memories at once.
        
        Args:
            updates: List of tuples (memory_id, update_dict)
            
        Returns:
            Tuple of (number of successfully updated memories, list of updated memory IDs)
        """
        success_count = 0
        updated_ids = []
        
        # Start a transaction
        self.memcore.table.conn.execute("BEGIN TRANSACTION")
        
        try:
            for memory_id, update_dict in updates:
                # Update memory
                success = self.memcore.update_memory(memory_id, update_dict)
                if success:
                    updated_ids.append(memory_id)
                    success_count += 1
            
            # Commit transaction
            self.memcore.table.conn.execute("COMMIT")
        except Exception as e:
            # Rollback on error
            self.memcore.table.conn.execute("ROLLBACK")
            raise e
        
        return success_count, updated_ids
    
    def batch_delete(self, memory_ids: List[str]) -> Tuple[int, List[str]]:
        """
        Delete multiple memories at once.
        
        Args:
            memory_ids: List of memory IDs to delete
            
        Returns:
            Tuple of (number of successfully deleted memories, list of deleted memory IDs)
        """
        success_count = 0
        deleted_ids = []
        
        # Start a transaction
        self.memcore.table.conn.execute("BEGIN TRANSACTION")
        
        try:
            for memory_id in memory_ids:
                # Delete memory
                success = self.memcore.delete_memory(memory_id)
                if success:
                    deleted_ids.append(memory_id)
                    success_count += 1
            
            # Commit transaction
            self.memcore.table.conn.execute("COMMIT")
        except Exception as e:
            # Rollback on error
            self.memcore.table.conn.execute("ROLLBACK")
            raise e
        
        return success_count, deleted_ids
    
    def batch_export(self, memory_ids: List[str], output_path: str) -> int:
        """
        Export specific memories to a JSON file.
        
        Args:
            memory_ids: List of memory IDs to export
            output_path: Path to output file
            
        Returns:
            Number of exported memories
        """
        memories = []
        
        for memory_id in memory_ids:
            memory = self.memcore.get_memory(memory_id)
            if memory:
                memories.append(memory.to_dict())
        
        with open(output_path, 'w') as f:
            json.dump(memories, f, indent=2)
        
        return len(memories)
    
    def export_query_results(self, query: str, output_path: str) -> int:
        """
        Export memories matching a MemQL query to a JSON file.
        
        Args:
            query: MemQL query
            output_path: Path to output file
            
        Returns:
            Number of exported memories
        """
        memories = self.memcore.memql_query(query)
        
        with open(output_path, 'w') as f:
            json.dump([memory.to_dict() for memory in memories], f, indent=2)
        
        return len(memories)
    
    def import_from_json(self, input_path: str, encrypted: bool = False) -> Tuple[int, List[str]]:
        """
        Import memories from a JSON file.
        
        Args:
            input_path: Path to input file
            encrypted: Whether to encrypt the memories
            
        Returns:
            Tuple of (number of imported memories, list of memory IDs)
        """
        with open(input_path, 'r') as f:
            memories = json.load(f)
        
        return self.batch_add(memories, encrypted=encrypted)
    
    def import_from_csv(self, input_path: str, encrypted: bool = False, 
                        has_header: bool = True) -> Tuple[int, List[str]]:
        """
        Import memories from a CSV file.
        
        Expected CSV format:
        content,tags,importance,source
        "Memory content","tag1,tag2",0.8,"source"
        
        Args:
            input_path: Path to input file
            encrypted: Whether to encrypt the memories
            has_header: Whether the CSV file has a header row
            
        Returns:
            Tuple of (number of imported memories, list of memory IDs)
        """
        memories = []
        
        with open(input_path, 'r', newline='') as f:
            reader = csv.reader(f)
            
            # Skip header if present
            if has_header:
                next(reader, None)
            
            for row in reader:
                if len(row) >= 1:
                    memory = {
                        "content": row[0],
                        "tags": row[1].split(',') if len(row) > 1 and row[1] else [],
                        "importance": float(row[2]) if len(row) > 2 and row[2] else 0.5,
                        "source": row[3] if len(row) > 3 else ""
                    }
                    memories.append(memory)
        
        return self.batch_add(memories, encrypted=encrypted)
    
    def import_from_text_folder(self, folder_path: str, encrypted: bool = False, 
                               recursive: bool = False, 
                               extension: str = ".txt") -> Tuple[int, List[str]]:
        """
        Import memories from text files in a folder.
        
        Args:
            folder_path: Path to folder containing text files
            encrypted: Whether to encrypt the memories
            recursive: Whether to search recursively in subfolders
            extension: File extension to look for
            
        Returns:
            Tuple of (number of imported memories, list of memory IDs)
        """
        memories = []
        
        # Get list of files
        if recursive:
            files = list(Path(folder_path).rglob(f"*{extension}"))
        else:
            files = list(Path(folder_path).glob(f"*{extension}"))
        
        for file_path in files:
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                
                # Use filename as tag
                filename = file_path.stem
                
                memory = {
                    "content": content,
                    "tags": [filename],
                    "importance": 0.5,
                    "source": str(file_path)
                }
                memories.append(memory)
            except Exception:
                # Skip files that can't be read
                continue
        
        return self.batch_add(memories, encrypted=encrypted)
    
    def tag_batch(self, memory_ids: List[str], tags: List[str], 
                 remove: bool = False) -> Tuple[int, List[str]]:
        """
        Add or remove tags from multiple memories.
        
        Args:
            memory_ids: List of memory IDs
            tags: List of tags to add or remove
            remove: Whether to remove the tags (False = add)
            
        Returns:
            Tuple of (number of updated memories, list of updated memory IDs)
        """
        updates = []
        
        for memory_id in memory_ids:
            memory = self.memcore.get_memory(memory_id)
            if not memory:
                continue
            
            current_tags = set(memory.tags)
            
            if remove:
                # Remove tags
                new_tags = list(current_tags - set(tags))
            else:
                # Add tags
                new_tags = list(current_tags.union(set(tags)))
            
            updates.append((memory_id, {"tags": new_tags}))
        
        return self.batch_update(updates)
    
    def update_importance_batch(self, memory_ids: List[str], 
                              importance: float) -> Tuple[int, List[str]]:
        """
        Update importance for multiple memories.
        
        Args:
            memory_ids: List of memory IDs
            importance: New importance value
            
        Returns:
            Tuple of (number of updated memories, list of updated memory IDs)
        """
        updates = [(memory_id, {"importance": importance}) for memory_id in memory_ids]
        return self.batch_update(updates)
    
    def process_in_chunks(self, items: List[Any], chunk_size: int = 100) -> Iterator[List[Any]]:
        """
        Process a list in chunks to avoid memory issues with large batches.
        
        Args:
            items: List of items to process
            chunk_size: Size of each chunk
            
        Returns:
            Iterator of chunks
        """
        for i in range(0, len(items), chunk_size):
            yield items[i:i + chunk_size]
