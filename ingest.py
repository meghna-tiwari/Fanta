import os
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone
from dotenv import load_dotenv
load_dotenv()

# ─── CONFIGURATION ──────────────────────────────────────────────────────────
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
INDEX_NAME = "test-dataset" # Must have 384 dimensions for MiniLM
NAMESPACE = "gold_data"                # Your "Expert Knowledge" room

# Initialize Embeddings (Local & Free)
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

def ingest_data(data_dir="./scraped_data"):
    
    pc = Pinecone(api_key=PINECONE_API_KEY)
    
    # Get all subdirectories (sponsorship, speakers, venues, etc.)
    categories = [d for d in os.listdir(data_dir) if os.path.isdir(os.path.join(data_dir, d))]
    
    all_chunks = []
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=100,
        separators=["\n\n", "\n", ". ", " ", ""]
    )

    for category in categories:
        print(f"--- Processing Category: {category} ---")
        loader = DirectoryLoader(os.path.join(data_dir, category), glob="*/*.txt", loader_cls=TextLoader)
        docs = loader.load()
        
        # Add metadata 'category' to each doc before splitting
        for doc in docs:
            doc.metadata["category"] = category
            
        chunks = text_splitter.split_documents(docs)
        all_chunks.extend(chunks)
        print(f"Created {len(chunks)} chunks for {category}.")

    # Upload to Pinecone
    print(f"\nUploading {len(all_chunks)} total chunks to Namespace: {NAMESPACE}...")
    PineconeVectorStore.from_documents(
        all_chunks,
        embeddings,
        index_name=INDEX_NAME,
        namespace=NAMESPACE,
        pinecone_api_key=PINECONE_API_KEY
    )
    print("Ingestion Complete!")

if __name__ == "__main__":
    # Ensure folders exist for testing
    # os.makedirs("./scraped_data/sponsorship", exist_ok=True)
    ingest_data()