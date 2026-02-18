import json
import os
from typing import List, Dict, Any
from dataclasses import asdict
from models import Paper, Experiment, Idea

class KnowledgeBase:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.papers_file = os.path.join(data_dir, "papers.json")
        self.experiments_file = os.path.join(data_dir, "experiments.json")
        self.ideas_file = os.path.join(data_dir, "ideas.json")
        self._ensure_data_dir()

    def _ensure_data_dir(self):
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

    def _load_data(self, filepath: str) -> List[Dict[str, Any]]:
        if not os.path.exists(filepath):
            return []
        with open(filepath, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []

    def _save_data(self, filepath: str, data: List[Dict[str, Any]]):
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def add_paper(self, paper: Paper):
        papers = self._load_data(self.papers_file)
        # Simple deduplication by title (case-insensitive)
        if any(p['title'].lower() == paper.title.lower() for p in papers):
            print(f"Paper '{paper.title}' already exists.")
            return
        papers.append(asdict(paper))
        self._save_data(self.papers_file, papers)
        print(f"Added paper: {paper.title}")

    def get_papers(self) -> List[Paper]:
        data = self._load_data(self.papers_file)
        return [Paper(**p) for p in data]

    def add_experiment(self, experiment: Experiment):
        experiments = self._load_data(self.experiments_file)
        experiments.append(asdict(experiment))
        self._save_data(self.experiments_file, experiments)
        print(f"Added experiment: {experiment.title}")

    def get_experiments(self) -> List[Experiment]:
        data = self._load_data(self.experiments_file)
        return [Experiment(**p) for p in data]
    
    def add_idea(self, idea: Idea):
        ideas = self._load_data(self.ideas_file)
        ideas.append(asdict(idea))
        self._save_data(self.ideas_file, ideas)
        print(f"Added idea: {idea.title}")

    def index_documents(self, source_dir: str = "data/knowledge"):
        """
        Index PDF and Markdown files from source_dir into ChromaDB.
        """
        import chromadb
        from chromadb.utils import embedding_functions
        
        if not os.path.exists(source_dir):
            os.makedirs(source_dir)
            print(f"Created knowledge directory: {source_dir}")
            return

        client = chromadb.PersistentClient(path=os.path.join(self.data_dir, "chroma_db"))
        # Use default lightweight embedding model (all-MiniLM-L6-v2) usually built-in or downloaded
        sentence_transformer_ef = embedding_functions.DefaultEmbeddingFunction()
        
        collection = client.get_or_create_collection(
            name="research_notes",
            embedding_function=sentence_transformer_ef
        )
        
        print(f"Scanning {source_dir} for knowledge...")
        ids = []
        documents = []
        metadatas = []
        
        for root, _, files in os.walk(source_dir):
            for file in files:
                filepath = os.path.join(root, file)
                content = ""
                
                if file.endswith(".md") or file.endswith(".txt"):
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                elif file.endswith(".pdf"):
                    try:
                        from pypdf import PdfReader
                        reader = PdfReader(filepath)
                        content = ""
                        for page in reader.pages:
                            content += page.extract_text() + "\n"
                    except Exception as e:
                        print(f"Failed to read PDF {file}: {e}")
                        continue
                
                if content:
                    # Simple chunking by 1000 chars for now
                    chunks = [content[i:i+1000] for i in range(0, len(content), 1000)]
                    for idx, chunk in enumerate(chunks):
                        ids.append(f"{file}_{idx}")
                        documents.append(chunk)
                        metadatas.append({"source": file, "chunk_id": idx})
        
        if documents:
            collection.upsert(ids=ids, documents=documents, metadatas=metadatas)
            print(f"Indexed {len(documents)} chunks from local knowledge base.")
        else:
            print("No documents found to index.")

    def query_similar_context(self, query: str, n_results: int = 3) -> str:
        """
        Retrieve relevant context from ChromaDB.
        """
        import chromadb
        from chromadb.utils import embedding_functions
        
        client = chromadb.PersistentClient(path=os.path.join(self.data_dir, "chroma_db"))
        sentence_transformer_ef = embedding_functions.DefaultEmbeddingFunction()
        
        try:
            collection = client.get_collection(name="research_notes", embedding_function=sentence_transformer_ef)
            results = collection.query(query_texts=[query], n_results=n_results)
            
            context = []
            if results['documents']:
                for idx, doc in enumerate(results['documents'][0]):
                     meta = results['metadatas'][0][idx]
                     context.append(f"[Source: {meta['source']}]\n{doc}")
            
            return "\n\n".join(context)
        except Exception:
            # Collection might not exist yet
            return ""

    def get_ideas(self) -> List[Idea]:
        data = self._load_data(self.ideas_file)
        return [Idea(**p) for p in data]
