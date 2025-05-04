from memco import MemCore, MemoryBuilder
from memco.embedding import get_embedding_provider

# Initialize the embedding provider
embedding_provider = get_embedding_provider()

# Create a memory system instance with vector search capabilities
mem_system = MemCore(
    root_path=".memfolder",
    encryption_key="my_secret_key",
    embedding_provider=embedding_provider
)

# Create a memory builder with the embedding provider
builder = MemoryBuilder(embedding_provider)

# Create a new memory record with automatic embedding generation
memory = builder.set_content("This is an example memory with vector embedding") \
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
print(f"Embedding length: {len(retrieved.embedding)}")

# Create more memories for vector search demo
builder.set_content("Artificial intelligence is transforming how we interact with technology") \
       .set_tags(["ai", "technology"]) \
       .set_importance(0.9) \
       .set_source("example.py")
mem_system.add_memory(builder.build())

builder.set_content("Vector search enables semantic similarity matching") \
       .set_tags(["vector", "search", "similarity"]) \
       .set_importance(0.85) \
       .set_source("example.py")
mem_system.add_memory(builder.build())

builder.set_content("Machine learning models can process natural language") \
       .set_tags(["ml", "nlp"]) \
       .set_importance(0.75) \
       .set_source("example.py")
mem_system.add_memory(builder.build())

# Perform a vector search
print("\nVector search results for 'AI technology':")
results = mem_system.vector_search_query("AI technology", top_k=2)
for i, memory in enumerate(results):
    print(f"{i+1}. {memory.content} (tags: {memory.tags})")
print("\nVector search results for 'Vectors':")
results = mem_system.vector_search_query("Vector", top_k=2)
for i, memory in enumerate(results):
    print(f"{i+1}. {memory.content} (tags: {memory.tags})")

# Use MemQL to query
print("\nMemQL query results:")
results = mem_system.memql_query("SELECT WHERE tags == \"vector\" ORDER BY importance DESC")
for i, memory in enumerate(results):
    print(f"{i+1}. {memory.content} (importance: {memory.importance})")

# Export to JSON
mem_system.export_json("memories_backup.json")
print("\nExported memories to memories_backup.json")

# Close connections
mem_system.close()
