from langchain_ollama import OllamaEmbeddings

embeddings = OllamaEmbeddings(
    model="mxbai-embed-large:latest",
    base_url="http://localhost:11434"
)

def embed_query(text: str):
    return embeddings.embed_query(text)



print("✅ Embeddings (Ollama model: 'mxbai-embed-large:latest') initialized successfully.")