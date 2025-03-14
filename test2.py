from sentence_transformers import SentenceTransformer

embed_model = SentenceTransformer("all-MiniLM-L6-v2")

text = "A system for healthcare alerts using Flask and Python."
vector = embed_model.encode(text)

print("Embedding shape:", vector.shape)  # Should print (384,) for MiniLM
print("First 5 values:", vector[:5])  # Print first few values to check
