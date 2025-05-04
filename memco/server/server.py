import os
import json
import uvicorn
from fastapi import FastAPI, HTTPException, Depends, Body, Security
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import threading
from dotenv import load_dotenv

from ..memco import MemCore, MemoryRecord, MemoryBuilder
from ..embedding import get_embedding_provider

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI(title="MemCore Server", description="A server for the MemCore memory system")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables
server_instance = None
memco_instance = None

# Models
class MemoryCreate(BaseModel):
    content: str
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    importance: Optional[float] = 0.5
    source: Optional[str] = ""
    encrypted: Optional[bool] = False

class MemoryUpdate(BaseModel):
    content: Optional[str] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    importance: Optional[float] = None
    source: Optional[str] = None

class MemoryResponse(BaseModel):
    id: str
    content: str
    tags: List[str]
    metadata: Dict[str, Any]
    importance: float
    created_at: float
    updated_at: float
    source: str

class MemQLQuery(BaseModel):
    query: str

class VectorSearchQuery(BaseModel):
    text: str
    top_k: Optional[int] = 5

api_keys_list = []

# Dependency for API key validation


from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-Key")

def get_api_key(api_key_header: str = Security(api_key_header)):
    if api_keys_list:
        if not api_key_header or api_key_header not in api_keys_list:
            raise HTTPException(status_code=401, detail="Invalid or missing API key")
    return api_key_header

# Dependency
def get_memco():
    if memco_instance is None:
        raise HTTPException(status_code=500, detail="MemCore instance not initialized")
    return memco_instance

# Routes
@app.get("/", dependencies=[Depends(get_api_key)])
def read_root():
    return {"message": "MemCore Server is running"}

@app.post("/memories", response_model=MemoryResponse, dependencies=[Depends(get_api_key)])
def create_memory(memory: MemoryCreate, memco: MemCore = Depends(get_memco)):
    builder = MemoryBuilder(memco.embedding_provider)
    if memory.content:
        builder.set_content(memory.content)
    if memory.tags:
        builder.set_tags(memory.tags)
    if memory.metadata:
        builder.set_metadata(memory.metadata)
    if memory.importance is not None:
        builder.set_importance(memory.importance)
    if memory.source:
        builder.set_source(memory.source)
    memory_record = builder.build()
    memory_id = memco.add_memory(memory_record, encrypted=memory.encrypted)
    data = memco.get_memory(memory_id).to_dict(True)
    print(data)
    return data

@app.get("/memories/{memory_id}", response_model=MemoryResponse, dependencies=[Depends(get_api_key)])
def get_memory(memory_id: str, memco: MemCore = Depends(get_memco)):
    memory = memco.get_memory(memory_id)
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
    
    return memory.to_dict()

@app.put("/memories/{memory_id}", response_model=MemoryResponse, dependencies=[Depends(get_api_key)])
def update_memory(memory_id: str, memory: MemoryUpdate, memco: MemCore = Depends(get_memco)):
    # Build update dictionary
    update_dict = {}
    if memory.content is not None:
        update_dict["content"] = memory.content
    if memory.tags is not None:
        update_dict["tags"] = memory.tags
    if memory.metadata is not None:
        update_dict["metadata"] = memory.metadata
    if memory.importance is not None:
        update_dict["importance"] = memory.importance
    if memory.source is not None:
        update_dict["source"] = memory.source
    
    # Update memory
    success = memco.update_memory(memory_id, update_dict)
    if not success:
        raise HTTPException(status_code=404, detail="Memory not found")
    
    return memco.get_memory(memory_id).to_dict()

@app.delete("/memories/{memory_id}", dependencies=[Depends(get_api_key)])
def delete_memory(memory_id: str, memco: MemCore = Depends(get_memco)):
    success = memco.delete_memory(memory_id)
    if not success:
        raise HTTPException(status_code=404, detail="Memory not found")
    
    return {"message": "Memory deleted successfully"}

@app.post("/query/memql", response_model=List[MemoryResponse], dependencies=[Depends(get_api_key)])
def query_memql(query: MemQLQuery, memco: MemCore = Depends(get_memco)):
    memories = memco.memql_query(query.query)
    return [memory.to_dict() for memory in memories]

@app.post("/query/vector", response_model=List[MemoryResponse], dependencies=[Depends(get_api_key)])
def query_vector(query: VectorSearchQuery, memco: MemCore = Depends(get_memco)):
    memories = memco.vector_search_query(query.text, query.top_k)
    return [memory.to_dict() for memory in memories]

@app.post("/export", dependencies=[Depends(get_api_key)])
def export_memories(output_path: str = Body(..., embed=True), memco: MemCore = Depends(get_memco)):
    count = memco.export_json(output_path)
    return {"message": f"Exported {count} memories to {output_path}"}

@app.post("/import", dependencies=[Depends(get_api_key)])
def import_memories(
    input_path: str = Body(..., embed=True),
    encrypt: bool = Body(False, embed=True),
    memco: MemCore = Depends(get_memco)
):
    count = memco.import_json(input_path, encrypt)
    return {"message": f"Imported {count} memories from {input_path}"}

# Server functions
def start_server(
    host: str = "0.0.0.0",
    port: int = 8000,
    mem_path: str = ".memfolder",
    encryption_key: Optional[str] = None
    ,
    api_keys: Optional[List[str]] = None
):
    """Start the MemCore server."""
    global memco_instance, api_keys_list

    # Set API keys
    api_keys_list = api_keys or []
    
    # Initialize MemCore
    memco_instance = MemCore(
        root_path=mem_path,
        encryption_key=encryption_key,
        embedding_provider=get_embedding_provider()
    )
    
    # Start server in a separate thread
    server_thread = threading.Thread(
        target=uvicorn.run,
        kwargs={"app": app, "host": host, "port": port}
    )
    server_thread.daemon = True
    server_thread.start()
    
    return server_thread

def stop_server():
    """Stop the MemCore server."""
    global memco_instance
    
    if memco_instance:
        memco_instance.close()
        memco_instance = None
