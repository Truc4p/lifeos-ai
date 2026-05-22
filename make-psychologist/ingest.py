#!/usr/bin/env python3
"""Index all markdown files in research-takeaways/ into ChromaDB.

Usage:
    python ingest.py           # add/update documents
    python ingest.py --reset   # wipe and rebuild from scratch
"""
import argparse
from dotenv import load_dotenv
from psychologist.loader import load_and_chunk
from psychologist.vectorstore import build_vectorstore

load_dotenv()


def main() -> None:
    parser = argparse.ArgumentParser(description="Index research takeaways into ChromaDB.")
    parser.add_argument("--reset", action="store_true", help="Wipe and rebuild the vector store")
    args = parser.parse_args()

    print("Loading research documents...")
    docs = load_and_chunk()
    unique_files = len({d.metadata["source_file"] for d in docs})
    print(f"  {len(docs)} chunks from {unique_files} file(s)")

    print("Embedding and indexing into ChromaDB...")
    build_vectorstore(docs)
    print(f"Done — {len(docs)} chunks indexed into chroma_db/")


if __name__ == "__main__":
    main()
