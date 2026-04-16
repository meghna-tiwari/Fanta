import json
import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter

load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
INDEX_NAME = "test-dataset"
NAMESPACE = "gold_data"
DEFAULT_DATASET = Path("master_event_data.json")
DEFAULT_DATA_DIR = Path("scraped_data")

_embeddings = None


def get_embeddings():
    global _embeddings
    if _embeddings is None:
        _embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    return _embeddings


def _safe_slug(value: str) -> str:
    return "".join(ch.lower() if ch.isalnum() else "_" for ch in value).strip("_") or "item"


def export_scraped_data(dataset_path: Path = DEFAULT_DATASET, output_dir: Path = DEFAULT_DATA_DIR) -> int:
    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset not found at {dataset_path}")

    with dataset_path.open("r", encoding="utf-8") as handle:
        dataset = json.load(handle)

    category_map = {
        "sponsors": ["sponsor", "sponsorship", "partner", "marketing spend"],
        "speakers": ["speaker", "artist", "performer", "agenda", "keynote"],
        "venues": ["venue", "location", "hall", "auditorium", "convention", "capacity"],
        "pricing": ["price", "ticket", "vip", "early bird", "registration fee", "pricing"],
        "gtm": ["community", "discord", "linkedin", "promotion", "marketing", "expo", "attendees"],
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    written = 0

    for category in category_map:
        (output_dir / category / "source").mkdir(parents=True, exist_ok=True)

    for index, event in enumerate(dataset):
        raw_content = str(event.get("raw_content", ""))
        haystack = raw_content.lower()
        header = "\n".join(
            [
                f"event_id: {event.get('event_id', index)}",
                f"category: {event.get('category', '')}",
                f"location: {event.get('location', '')}",
                f"url: {event.get('url', '')}",
                "",
            ]
        )

        for category, keywords in category_map.items():
            if any(keyword in haystack for keyword in keywords):
                filename = f"{index:04d}_{_safe_slug(str(event.get('event_id', index)))}.txt"
                target = output_dir / category / "source" / filename
                with target.open("w", encoding="utf-8") as handle:
                    handle.write(header + raw_content)
                written += 1

    return written


def ingest_data(data_dir: str = "./scraped_data") -> int:
    categories = [d for d in os.listdir(data_dir) if os.path.isdir(os.path.join(data_dir, d))]
    all_chunks = []

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=100,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    for category in categories:
        print(f"--- Processing Category: {category} ---")
        loader = DirectoryLoader(
            os.path.join(data_dir, category),
            glob="*/*.txt",
            loader_cls=TextLoader,
            loader_kwargs={"encoding": "utf-8"},
        )
        docs = loader.load()

        for doc in docs:
            doc.metadata["category"] = category

        chunks = text_splitter.split_documents(docs)
        all_chunks.extend(chunks)
        print(f"Created {len(chunks)} chunks for {category}.")

    print(f"\nUploading {len(all_chunks)} total chunks to Namespace: {NAMESPACE}...")
    PineconeVectorStore.from_documents(
        all_chunks,
        get_embeddings(),
        index_name=INDEX_NAME,
        namespace=NAMESPACE,
        pinecone_api_key=PINECONE_API_KEY,
    )
    print("Ingestion Complete!")
    return len(all_chunks)


if __name__ == "__main__":
    exported = export_scraped_data()
    print(f"Prepared {exported} text files in {DEFAULT_DATA_DIR}.")
    ingest_data()
