# MemCore Architecture

This document provides an overview of the MemCore architecture, explaining the key components and their interactions.

## System Overview

MemCore is designed as a modular memory management system with the following key components:

1. **Core Memory System**: Manages memory records and provides CRUD operations
2. **Vector Search**: Enables semantic similarity search using embeddings
3. **MemQL**: Query language for structured memory retrieval
4. **Storage Layer**: Handles persistence and retrieval of memories
5. **API Layer**: Provides programmatic access through CLI and REST API
6. **Client Libraries**: Simplifies integration with applications

## Component Details

### Core Memory System

The core memory system is responsible for managing memory records. It provides:

- Memory record creation, retrieval, updating, and deletion
- Memory history tracking for auditing changes
- Encryption for sensitive memory content
- Batch operations for efficient processing

Key classes:
- `MemoryRecord`: Represents a single memory with content, metadata, and embedding
- `MemoryBuilder`: Builder pattern for creating memory records
- `MemTable`: Handles database operations for memories
- `MemHistory`: Tracks changes to memories over time
- `MemCore`: Main class that orchestrates all components

### Vector Search

The vector search component enables semantic similarity search using embeddings:

- Cosine similarity calculation between embeddings
- Top-K retrieval of similar memories
- Integration with embedding providers (OpenAI, Cohere)

Key classes:
- `VectorSearch`: Manages vector storage and similarity search
- `EmbeddingProvider`: Abstract interface for embedding generation
- `OpenAIEmbedding`: Implementation for OpenAI embeddings
- `CohereEmbedding`: Implementation for Cohere embeddings

### MemQL

MemQL is a query language for structured memory retrieval:

- SQL-like syntax for familiarity
- Support for filtering, sorting, and limiting results
- Special handling for tags and metadata fields

Key components:
- `Parser`: Parses MemQL queries into an abstract syntax tree
- `Executor`: Executes queries against the memory store
- `Query`: Represents a parsed query with conditions and options

### Storage Layer

The storage layer handles persistence and retrieval of memories:

- SQLite database for local storage
- JSON serialization for import/export
- Encryption for sensitive data

Key features:
- Efficient indexing for fast retrieval
- Transaction support for atomic operations
- Backup and restore functionality

### API Layer

The API layer provides programmatic access to MemCore:

- CLI for command-line operations
- REST API for network access
- WebSocket support for real-time updates (planned)

Key components:
- `CLI`: Command-line interface with rich output
- `Server`: REST API server with FastAPI (Python)
- `Middleware`: Authentication and request processing

### Client Libraries

Client libraries simplify integration with applications:

- Python client for Python applications
- JavaScript client (planned)

## Data Flow

1. **Memory Creation**:
   - Application creates a memory using the client library
   - Memory is processed (embedding generation, encryption)
   - Memory is stored in the database
   - Memory ID is returned to the application

2. **Memory Retrieval**:
   - Application requests a memory by ID
   - Memory is retrieved from the database
   - Memory is decrypted if necessary
   - Memory is returned to the application

3. **Vector Search**:
   - Application provides query text
   - Embedding is generated for the query
   - Vector search finds similar memories
   - Results are returned to the application

4. **MemQL Query**:
   - Application provides a MemQL query
   - Query is parsed into an abstract syntax tree
   - Query is executed against the database
   - Results are returned to the application

## Architecture Diagrams

### Component Diagram

\`\`\`
+----------------+      +----------------+      +----------------+
|                |      |                |      |                |
|  Application   |<---->|  Client Lib    |<---->|  MemCore API   |
|                |      |                |      |                |
+----------------+      +----------------+      +-------+--------+
                                                        |
                                                        v
                                               +--------+--------+
                                               |                 |
                                               |  MemCore Core   |
                                               |                 |
                                               +--------+--------+
                                                        |
                        +---------------------------+---+---+---------------------------+
                        |                           |       |                           |
                +-------v-------+           +-------v-------+           +-------v-------+
                |               |           |               |           |               |
                |  Vector Search |           |    MemQL      |           |  Storage Layer |
                |               |           |               |           |               |
                +---------------+           +---------------+           +---------------+
\`\`\`

### Data Flow Diagram

\`\`\`
+-------------+     +-------------+     +-------------+     +-------------+
|             |     |             |     |             |     |             |
|  User Input  +---->  Client Lib  +---->  API Layer   +---->  Core System |
|             |     |             |     |             |     |             |
+-------------+     +-------------+     +-------------+     +------+------+
                                                                  |
                                                                  v
                                                           +------+------+
                                                           |             |
                                                           |  Processing  |
                                                           |             |
                                                           +------+------+
                                                                  |
                                                                  v
                                                           +------+------+
                                                           |             |
                                                           |  Storage DB  |
                                                           |             |
                                                           +-------------+
\`\`\`

## Future Architecture Considerations

As MemCore evolves, we're considering the following architectural changes:

1. **Distributed Mode**: Sharding for large memory collections
2. **Pluggable Storage**: Support for different storage backends
3. **Event System**: Pub/sub for memory changes
4. **Memory Federation**: Protocol for sharing memories across systems

These changes will be implemented incrementally while maintaining backward compatibility.
