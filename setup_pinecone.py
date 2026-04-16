import os
import time
from pinecone import Pinecone, ServerlessSpec
from dotenv import load_dotenv

# 1. Load API key
load_dotenv()
api_key = os.getenv("PINECONE_API_KEY")

if not api_key:
    raise ValueError("❌ PINECONE_API_KEY not found in .env file")

# 2. Initialize Pinecone
pc = Pinecone(api_key=api_key)

# 3. Config
INDEX_NAME = "test-dataset"   # use hyphens (safer than underscores)
DIMENSION = 384
METRIC = "cosine"

def create_index():
    # 🔥 FIX 1: list_indexes() format changed
    existing_indexes = [index.name for index in pc.list_indexes()]

    if INDEX_NAME in existing_indexes:
        print(f"✅ Index '{INDEX_NAME}' already exists")
        return

    print(f"🚀 Creating index '{INDEX_NAME}'...")

    pc.create_index(
        name=INDEX_NAME,
        dimension=DIMENSION,
        metric=METRIC,
        spec=ServerlessSpec(
            cloud="aws",
            region="us-east-1"
        )
    )

    # 🔥 FIX 2: describe_index returns object, not dict
    print("⏳ Waiting for index to be ready...")
    while True:
        desc = pc.describe_index(INDEX_NAME)
        if desc.status.ready:
            break
        time.sleep(2)

    print(f"🎉 Index '{INDEX_NAME}' is ready!")

if __name__ == "__main__":
    create_index()