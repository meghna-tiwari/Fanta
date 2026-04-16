import os
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_pinecone import PineconeVectorStore
from dotenv import load_dotenv
import os

load_dotenv()
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
# ─── CONFIGURATION ──────────────────────────────────────────────────────────
INDEX_NAME = "test-dataset"
DEFAULT_NAMESPACE = "gold_data"

# Initialize same embedding model used in ingestion
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

def retrieve_context(query: str, category: str, top_k: int = 10, namespace: str = DEFAULT_NAMESPACE) -> str:
    """
    Search Pinecone for relevant chunks filtered by category.
    This matches the signature expected by agents.py.
    """
    try:
        # Connect to the existing index
        vectorstore = PineconeVectorStore(
            index_name=INDEX_NAME,
            embedding=embeddings,
            namespace=namespace,
            pinecone_api_key=PINECONE_API_KEY
        )

        # Perform search with metadata filter
        # This ensures the Sponsor Agent ONLY sees 'sponsorship' data
        results = vectorstore.similarity_search(
            query,
            k=top_k,
            filter={"category": category}
        )

        # Convert list of Document objects into a single clean string for the LLM
        context_text = "\n---\n".join([doc.page_content for doc in results])
        
        if not context_text:
            return f"No specific data found for category: {category}."
            
        return context_text

    except Exception as e:
        print(f"[ERROR] Retrieval failed: {e}")
        return "Error retrieving context from database."

# Quick test if run directly
if __name__ == "__main__":
    test_context = retrieve_context("Who are the top AI sponsors?", "sponsorship")
    print(test_context)