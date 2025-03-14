from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

# Load Embedding Model
model = SentenceTransformer("all-MiniLM-L6-v2")

# Sample project descriptions
projects = [
    {"name": "Digital Medics", "description": "A system for healthcare alerts using Flask and Python."},
    {"name": "Puzzle Vault", "description": "Escape room game using React and Flask."}
]

# Convert Descriptions to Vectors
vectors = np.array([model.encode(p["description"]) for p in projects])
index = faiss.IndexFlatL2(vectors.shape[1])
index.add(vectors)

# Search Function
def search_projects(query):
    query_vector = model.encode([query])
    D, I = index.search(query_vector, k=3)
    results = [projects[i] for i in I[0]]
    return results

print(search_projects("healthcare system using Flask"))
