from qdrant_client import QdrantClient

# Connect to local Qdrant instance
client = QdrantClient(host="localhost", port=6333)

# Create a collection
client.recreate_collection(
    collection_name="test_collection",
    vectors_config={"size": 384, "distance": "Cosine"}
)

# Insert a vector (example: embedding for 'hello world')
vector = [0.1] * 384
client.upsert(
    collection_name="test_collection",
    points=[{"id": 1, "vector": vector, "payload": {"text": "hello world"}}]
)

# Search for similar vectors
results = client.search(
    collection_name="test_collection",
    query_vector=vector,
    limit=3
)
print(results)
