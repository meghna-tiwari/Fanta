import os

from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_pinecone import PineconeVectorStore

load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
INDEX_NAME = "test-dataset"
DEFAULT_NAMESPACE = "gold_data"

_embeddings = None


def get_embeddings():
    global _embeddings
    if _embeddings is None:
        _embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    return _embeddings


def retrieve_context(query: str, category: str, top_k: int = 10, namespace: str = DEFAULT_NAMESPACE) -> str:
    try:
        vectorstore = PineconeVectorStore(
            index_name=INDEX_NAME,
            embedding=get_embeddings(),
            namespace=namespace,
            pinecone_api_key=PINECONE_API_KEY,
        )

        results = vectorstore.similarity_search(
            query,
            k=top_k,
            filter={"category": category},
        )

        context_text = "\n---\n".join([doc.page_content for doc in results])
        if not context_text:
            return f"No specific data found for category: {category}."
        return context_text
    except Exception as exc:
        print(f"[ERROR] Retrieval failed: {exc}")
        return "Error retrieving context from database."


if __name__ == "__main__":
    test_context = retrieve_context("Who are the top AI sponsors?", "sponsors")
    print(test_context)
