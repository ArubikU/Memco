import os
import json
import sqlite3
import numpy as np
from typing import List, Dict, Any, Optional, NamedTuple

class VectorSearchResult(NamedTuple):
    """
    Result of a vector search operation.
    """
    id: str
    score: float
    metadata: Dict[str, Any]

class VectorSearch:
    """
    Manages vector search functionality for the MemCore system.
    """
    def __init__(self, path: str):
        self.path = path
        os.makedirs(path, exist_ok=True)
        self.db_path = os.path.join(path, "vectors.db")
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._initialize_db()
        self.rng = np.random.RandomState(42)  # For reproducibility
    
    def _initialize_db(self):
        """Initialize the database schema."""
        cursor = self.conn.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS vectors (
            id TEXT PRIMARY KEY,
            vector TEXT,
            metadata TEXT
        )
        ''')
        self.conn.commit()
    
    def add_vector(self, id: str, vector: List[float], metadata: Dict[str, Any] = None) -> bool:
        """Add a vector to the database."""
        cursor = self.conn.cursor()
        try:
            cursor.execute(
                'INSERT INTO vectors VALUES (?, ?, ?)',
                (
                    id,
                    json.dumps(vector),
                    json.dumps(metadata or {})
                )
            )
            self.conn.commit()
            return True
        except Exception:
            return False
    
    def update_vector(self, id: str, vector: List[float], metadata: Dict[str, Any] = None) -> bool:
        """Update a vector in the database."""
        cursor = self.conn.cursor()
        try:
            cursor.execute(
                'UPDATE vectors SET vector = ?, metadata = ? WHERE id = ?',
                (
                    json.dumps(vector),
                    json.dumps(metadata or {}),
                    id
                )
            )
            self.conn.commit()
            return cursor.rowcount > 0
        except Exception:
            return False
    
    def delete_vector(self, id: str) -> bool:
        """Delete a vector from the database."""
        cursor = self.conn.cursor()
        try:
            cursor.execute('DELETE FROM vectors WHERE id = ?', (id,))
            self.conn.commit()
            return cursor.rowcount > 0
        except Exception:
            return False
    
    def get_vector(self, id: str) -> Optional[Dict[str, Any]]:
        """Get a vector by ID."""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM vectors WHERE id = ?', (id,))
        row = cursor.fetchone()
        
        if not row:
            return None
        
        return {
            "id": row[0],
            "vector": json.loads(row[1]),
            "metadata": json.loads(row[2])
        }
    
    def search(self, query_vector: List[float], top_k: int = 5) -> List[VectorSearchResult]:
        """
        Search for vectors similar to the query vector.
        Uses cosine similarity for the search.
        """
        cursor = self.conn.cursor()
        cursor.execute('SELECT id, vector, metadata FROM vectors')
        rows = cursor.fetchall()
        
        if not rows:
            return []
        
        # Convert query vector to numpy array
        query_np = np.array(query_vector)
        
        # Calculate similarities
        similarities = []
        for row in rows:
            vector = np.array(json.loads(row[1]))
            
            # Calculate cosine similarity
            similarity = self._cosine_similarity(query_np, vector)
            
            similarities.append((row[0], similarity, json.loads(row[2])))
        
        # Sort by similarity (highest first)
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        # Return top_k results
        return [
            VectorSearchResult(id=id, score=score, metadata=metadata)
            for id, score, metadata in similarities[:top_k]
        ]
    
    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors."""
        # Handle zero vectors
        if np.all(a == 0) or np.all(b == 0):
            return 0.0
        
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
    
    
    def _compress_vector(self, vector: np.ndarray, level: int = 10) -> np.ndarray:
    
        target_dim = len(vector) // level
        # Generate random projection matrix (Gaussian)
        projection_matrix = self.rng.randn(len(vector), target_dim) / np.sqrt(target_dim)
        
        # Project the vector
        compressed = np.dot(vector, projection_matrix)
        return compressed
    def close(self):
        """Close the database connection."""
        self.conn.close()
