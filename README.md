# MemCore

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Version](https://img.shields.io/badge/version-1.0.0-green.svg)

A complete memory management system with vector search capabilities, designed for efficient storage, retrieval, and handling of information.

## 🚀 Features

* **Full Memory System**: Complete CRUD operations for memory records
* **Vector Search**: Semantic similarity search using embeddings
* **MemQL**: A custom query language for structured memory retrieval
* **Secure Storage**: Built-in encryption for sensitive content
* **Versatile API**: Programmatic access via CLI and REST API
* **Client Libraries**: Easy integration with applications

## 📋 Requirements

* Python 3.7+
* Dependencies listed in `setup.py`

## 🔧 Installation

### From PyPI

```bash
pip install memcore
```

### From Source

```bash
git clone https://github.com/memco/memcore.git
cd memcore
pip install -e .
```

## 🏁 Getting Started

### Basic Example

```python
from memcore import MemCore, MemoryBuilder
from memcore.embedding import get_embedding_provider

# Initialize the embedding provider
embedding_provider = get_embedding_provider()

# Create an instance of the memory system with vector search capabilities
mem_system = MemCore(
    root_path=".memfolder",
    encryption_key="my_secret_key",
    embedding_provider=embedding_provider
)

# Create a memory builder with the embedding provider
builder = MemoryBuilder(embedding_provider)

# Create a new memory record with auto-generated embeddings
memory = builder.set_content("This is a memory example with vector embedding") \
                .set_tags(["example", "vector", "embedding"]) \
                .set_importance(0.8) \
                .set_source("example.py") \
                .build()

# Add the memory to the system
memory_id = mem_system.add_memory(memory, encrypted=True)
print(f"Memory created with ID: {memory_id}")

# Retrieve the memory
retrieved = mem_system.get_memory(memory_id)
print(f"Content: {retrieved.content}")
```

### Using the Client

```python
from memcore_client import MemCoreClient

# Initialize the client
client = MemCoreClient("http://localhost:8000")

# Add a memory
memory = client.add_memory(
    content="This is a test memory",
    tags=["test", "example"],
    importance=0.8,
    source="example.py"
)

# Search for similar memories
similar = client.vector_search("test memory")
print(f"Found {len(similar)} similar memories")

# Execute a MemQL query
results = client.memql_query("SELECT WHERE tags == \"test\" ORDER BY importance DESC")
print(f"The query returned {len(results)} memories")
```

## 📚 Architecture

MemCore is designed as a modular memory management system with the following key components:

1. **Core Memory System**: Manages memory records and provides CRUD operations
2. **Vector Search**: Enables semantic similarity search using embeddings
3. **MemQL**: Query language for structured memory retrieval
4. **Storage Layer**: Handles memory persistence and recovery
5. **API Layer**: Provides programmatic access via CLI and REST API
6. **Client Libraries**: Simplifies integration with applications

For more details, see [ARCHITECTURE.md](ARCHITECTURE.md).

## 🗺️ Roadmap

We're continuously improving MemCore. These are our goals for upcoming versions:

### v1.1.0 (June 2025)

* **Advanced Compression**
* **Synchronization System**
* **Performance Optimizations**

### v1.2.0 (July 2025)

* **Enhanced Security**
* **Advanced MemQL Features**
* **UI Components**

For more details, see [ROADMAP.md](ROADMAP.md).

## 👥 Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on how to contribute to the project.

We're currently focusing on:

1. Advanced compression implementation
2. Synchronization system
3. Performance improvements for large datasets
4. Better documentation and examples

## 📄 License

This project is licensed under the MIT License – see the [LICENSE](LICENSE) file for details.

```
MIT License

Copyright (c) 2025 MemCore Team

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```