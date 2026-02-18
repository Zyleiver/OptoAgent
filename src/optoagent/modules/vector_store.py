"""
ChromaDB-based vector store for RAG (Retrieval-Augmented Generation).

Handles document indexing and semantic similarity search.
"""

import os
from typing import List

from optoagent.config import DATA_DIR
from optoagent.logger import get_logger

logger = get_logger(__name__)


class VectorStore:
    """Manages ChromaDB vector indexing and retrieval for the knowledge base."""

    def __init__(self, data_dir: str | None = None):
        self.data_dir = data_dir or DATA_DIR
        self.db_path = os.path.join(self.data_dir, "chroma_db")
        self.knowledge_dir = os.path.join(self.data_dir, "knowledge")

    def _get_collection(self):
        """Get or create the ChromaDB collection."""
        import chromadb
        from chromadb.utils import embedding_functions

        client = chromadb.PersistentClient(path=self.db_path)
        ef = embedding_functions.DefaultEmbeddingFunction()
        return client.get_or_create_collection(
            name="research_notes",
            embedding_function=ef,
        )

    @staticmethod
    def _read_text_file(filepath: str) -> str:
        """Read a text file, trying multiple encodings."""
        for enc in ("utf-8", "utf-8-sig", "utf-16", "gbk", "latin-1"):
            try:
                with open(filepath, "r", encoding=enc) as f:
                    return f.read()
            except (UnicodeDecodeError, UnicodeError):
                continue
        logger.warning("Could not decode file %s with any encoding, skipping.", filepath)
        return ""

    def index_documents(self, source_dir: str | None = None) -> None:
        """
        Index PDF and Markdown files from source_dir into ChromaDB.
        Files are chunked at 1000 characters and embedded with all-MiniLM-L6-v2.
        """
        source_dir = source_dir or self.knowledge_dir

        if not os.path.exists(source_dir):
            os.makedirs(source_dir, exist_ok=True)
            logger.info("Created knowledge directory: %s", source_dir)
            return

        collection = self._get_collection()

        logger.info("Scanning %s for knowledge...", source_dir)
        ids: List[str] = []
        documents: List[str] = []
        metadatas: List[dict] = []

        for root, _, files in os.walk(source_dir):
            for file in files:
                filepath = os.path.join(root, file)
                content = ""

                if file.endswith((".md", ".txt")):
                    content = self._read_text_file(filepath)
                elif file.endswith(".pdf"):
                    try:
                        from pypdf import PdfReader

                        reader = PdfReader(filepath)
                        content = "\n".join(page.extract_text() for page in reader.pages)
                    except Exception as e:
                        logger.warning("Failed to read PDF %s: %s", file, e)
                        continue

                if content:
                    chunks = [content[i : i + 1000] for i in range(0, len(content), 1000)]
                    for idx, chunk in enumerate(chunks):
                        ids.append(f"{file}_{idx}")
                        documents.append(chunk)
                        metadatas.append({"source": file, "chunk_id": idx})

        if documents:
            collection.upsert(ids=ids, documents=documents, metadatas=metadatas)
            logger.info("Indexed %d chunks from local knowledge base.", len(documents))
        else:
            logger.info("No documents found to index.")

    def query_similar_context(self, query: str, n_results: int = 3) -> str:
        """Retrieve relevant context from ChromaDB as a single string."""
        try:
            import chromadb
            from chromadb.utils import embedding_functions

            client = chromadb.PersistentClient(path=self.db_path)
            ef = embedding_functions.DefaultEmbeddingFunction()
            collection = client.get_collection(name="research_notes", embedding_function=ef)

            results = collection.query(query_texts=[query], n_results=n_results)

            context_parts = []
            if results["documents"]:
                for idx, doc in enumerate(results["documents"][0]):
                    meta = results["metadatas"][0][idx]
                    context_parts.append(f"[Source: {meta['source']}]\n{doc}")

            return "\n\n".join(context_parts)
        except Exception:
            # Collection might not exist yet
            return ""
