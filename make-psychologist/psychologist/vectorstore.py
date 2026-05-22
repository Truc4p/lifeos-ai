import os
import shutil
from typing import List
from langchain_core.embeddings import Embeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from google import genai
from .config import EMBED_MODEL, CHROMA_DIR, COLLECTION, RETRIEVAL_K


class GeminiEmbeddings(Embeddings):
    """Thin wrapper around the google-genai SDK for batch-correct embeddings."""

    def __init__(self, model: str = EMBED_MODEL):
        self._model = model
        self._client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        response = self._client.models.embed_content(
            model=self._model,
            contents=texts,
        )
        return [e.values for e in response.embeddings]

    def embed_query(self, text: str) -> List[float]:
        response = self._client.models.embed_content(
            model=self._model,
            contents=[text],
        )
        return response.embeddings[0].values


def get_embeddings() -> GeminiEmbeddings:
    return GeminiEmbeddings()


def get_vectorstore() -> Chroma:
    return Chroma(
        collection_name=COLLECTION,
        embedding_function=get_embeddings(),
        persist_directory=str(CHROMA_DIR),
    )


def build_vectorstore(documents: list[Document]) -> Chroma:
    """Wipe and rebuild the vector store from a list of documents."""
    if CHROMA_DIR.exists():
        shutil.rmtree(CHROMA_DIR)
    return Chroma.from_documents(
        documents=documents,
        embedding=get_embeddings(),
        collection_name=COLLECTION,
        persist_directory=str(CHROMA_DIR),
    )


def get_retriever(vectorstore: Chroma):
    return vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": RETRIEVAL_K},
    )
