import os

from dotenv import load_dotenv
from pinecone import Pinecone

load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
INDEX_NAME = "test-dataset"
NAMESPACE = "gold_data"


def clear_namespace() -> None:
    if not PINECONE_API_KEY:
        raise ValueError("PINECONE_API_KEY not found in environment.")

    pc = Pinecone(api_key=PINECONE_API_KEY)
    index = pc.Index(INDEX_NAME)
    index.delete(delete_all=True, namespace=NAMESPACE)
    print(f"Cleared all vectors from index '{INDEX_NAME}' namespace '{NAMESPACE}'.")


if __name__ == "__main__":
    clear_namespace()
