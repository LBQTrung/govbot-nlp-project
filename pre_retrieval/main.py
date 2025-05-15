import os
from dotenv import load_dotenv
from pymongo import MongoClient
from sentence_transformers import SentenceTransformer
from pyvi.ViTokenizer import tokenize
import chromadb
from chromadb.config import Settings
from rank_bm25 import BM25Okapi
import numpy as np
from typing import List, Dict, Any, Tuple
import pickle
from pathlib import Path
from tqdm import tqdm

def load_environment() -> Tuple[str, str, str]:
    """Load environment variables for MongoDB connection"""
    load_dotenv()
    mongo_uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017')
    db_name = os.getenv('DB_NAME', 'your_database_name')
    collection_name = os.getenv('COLLECTION_NAME', 'your_collection_name')
    return mongo_uri, db_name, collection_name

def connect_mongodb(mongo_uri: str, db_name: str, collection_name: str) -> Tuple[MongoClient, Any]:
    """Connect to MongoDB and return client and collection"""
    client = MongoClient(mongo_uri)
    db = client[db_name]
    collection = db[collection_name]
    return client, collection

def initialize_chromadb() -> Tuple[chromadb.Client, Any]:
    """Initialize ChromaDB client and collection"""
    chroma_client = chromadb.PersistentClient(path="./chroma_db")
    
    chroma_collection = chroma_client.get_or_create_collection(
        name="thu_tuc_collection",
        metadata={"hnsw:space": "cosine"}
    )
    return chroma_client, chroma_collection

def load_embedding_model() -> SentenceTransformer:
    """Load Vietnamese embedding model"""
    return SentenceTransformer('./vietnamese-embedding')

def save_bm25_index(bm25_index: BM25Okapi, documents: List[List[str]], ids: List[str]):
    """Save BM25 index and associated data to disk"""
    BM25_INDEX_DIR = Path("./bm25_index")
    BM25_INDEX_DIR.mkdir(exist_ok=True)
    
    BM25_INDEX_PATH = BM25_INDEX_DIR / "bm25_index.pkl"
    BM25_DOCS_PATH = BM25_INDEX_DIR / "bm25_docs.pkl"
    BM25_IDS_PATH = BM25_INDEX_DIR / "bm25_ids.pkl"
    
    with open(BM25_INDEX_PATH, 'wb') as f:
        pickle.dump(bm25_index, f)
    with open(BM25_DOCS_PATH, 'wb') as f:
        pickle.dump(documents, f)
    with open(BM25_IDS_PATH, 'wb') as f:
        pickle.dump(ids, f)

def load_bm25_index() -> Tuple[BM25Okapi, List[List[str]], List[str]]:
    """Load BM25 index and associated data from disk"""
    BM25_INDEX_DIR = Path("./bm25_index")
    BM25_INDEX_PATH = BM25_INDEX_DIR / "bm25_index.pkl"
    BM25_DOCS_PATH = BM25_INDEX_DIR / "bm25_docs.pkl"
    BM25_IDS_PATH = BM25_INDEX_DIR / "bm25_ids.pkl"
    
    if not all(path.exists() for path in [BM25_INDEX_PATH, BM25_DOCS_PATH, BM25_IDS_PATH]):
        return None, [], []
    
    with open(BM25_INDEX_PATH, 'rb') as f:
        bm25_index = pickle.load(f)
    with open(BM25_DOCS_PATH, 'rb') as f:
        documents = pickle.load(f)
    with open(BM25_IDS_PATH, 'rb') as f:
        ids = pickle.load(f)
    
    return bm25_index, documents, ids

def process_documents(
    collection: Any,
    model: SentenceTransformer,
    chroma_collection: Any,
    chroma_client: chromadb.Client,
    filter_query: Dict = {"co_quan_ban_hanh": "Bộ Công an"}
) -> Tuple[BM25Okapi, List[List[str]], List[str]]:
    """Process documents from MongoDB and create embeddings and BM25 index"""
    total_docs = collection.count_documents(filter_query)
    print(f"Found {total_docs} documents in MongoDB")
    documents = collection.find(filter_query, {"ten_thu_tuc": 1, "_id": 1})
    
    bm25_documents = []
    bm25_ids = []
    ids = []
    documents_text = []
    metadatas = []
    
    pbar = tqdm(total=total_docs, desc="Processing documents", unit="doc")
    
    for doc in documents:
        if "ten_thu_tuc" in doc:
            # Tokenize the text
            tokenized_text = tokenize(doc["ten_thu_tuc"])
            
            # Create embedding
            embedding = model.encode([tokenized_text])[0]
            
            # Prepare data for ChromaDB
            doc_id = str(doc["_id"])
            ids.append(doc_id)
            documents_text.append(doc["ten_thu_tuc"])
            metadatas.append({"original_id": doc_id})
            
            # Prepare data for BM25
            bm25_documents.append(tokenized_text.split())
            bm25_ids.append(doc_id)
            
            # Add to ChromaDB
            chroma_collection.add(
                ids=[doc_id],
                embeddings=[embedding.tolist()],
                documents=[doc["ten_thu_tuc"]],
                metadatas=[{"original_id": doc_id}]
            )
        pbar.update(1)
    pbar.close()
    
    # Create and save BM25 index
    bm25 = BM25Okapi(bm25_documents)
    save_bm25_index(bm25, bm25_documents, bm25_ids)
    print(f"Successfully created and saved BM25 index with {len(bm25_documents)} documents")
    
    return bm25, bm25_documents, bm25_ids

def hybrid_search(
    query_text: str,
    model: SentenceTransformer,
    bm25: BM25Okapi,
    bm25_ids: List[str],
    chroma_collection: Any,
    n_results: int = 10,
    vector_weight: float = 0.7,
    bm25_weight: float = 0.3
) -> List[Dict[str, Any]]:
    """Perform hybrid search combining BM25 and vector search"""
    print("Processing search query...")
    # Tokenize query
    tokenized_query = tokenize(query_text)
    query_tokens = tokenized_query.split()
    
    print("Performing vector search...")
    # Vector search
    query_embedding = model.encode([tokenized_query])[0]
    vector_results = chroma_collection.query(
        query_embeddings=[query_embedding.tolist()],
        n_results=n_results * 2  # Get more results for better combination
    )
    
    print("Performing BM25 search...")
    # BM25 search
    bm25_scores = bm25.get_scores(query_tokens)
    
    # Create a mapping of document IDs to their scores
    combined_scores = {}
    
    # Process vector search results
    for i, doc_id in enumerate(tqdm(vector_results['ids'][0], desc="Processing vector results", unit="doc")):
        vector_score = vector_results['distances'][0][i]
        vector_score = 1 - (vector_score / 2)  # Normalize to 0-1
        combined_scores[doc_id] = vector_score * vector_weight
    
    # Process BM25 results for all documents
    print("Normalizing BM25 scores...")
    # Get all BM25 scores and normalize them
    bm25_scores_dict = {doc_id: score for doc_id, score in zip(bm25_ids, bm25_scores)}
    
    # Normalize BM25 scores to 0-1 range
    if len(bm25_scores) > 0:  # Check if we have any scores
        min_score = float(bm25_scores.min())  # Convert to float
        max_score = float(bm25_scores.max())  # Convert to float
        score_range = max_score - min_score
        
        if score_range > 0:  # Only normalize if there's a range
            for doc_id, score in bm25_scores_dict.items():
                normalized_score = float(score - min_score) / score_range  # Convert to float
                if doc_id in combined_scores:
                    combined_scores[doc_id] += normalized_score * bm25_weight
                else:
                    combined_scores[doc_id] = normalized_score * bm25_weight
        else:
            # If all scores are the same, give them equal weight
            equal_score = 1.0 / len(bm25_scores)
            for doc_id in bm25_ids:
                if doc_id in combined_scores:
                    combined_scores[doc_id] += equal_score * bm25_weight
                else:
                    combined_scores[doc_id] = equal_score * bm25_weight
    
    print("Sorting and preparing final results...")
    # Sort by combined scores
    sorted_results = sorted(
        combined_scores.items(),
        key=lambda x: x[1],
        reverse=True
    )[:n_results]
    
    # Prepare final results
    final_results = []
    for doc_id, score in sorted_results:
        # Get document from vector results if available, otherwise from BM25
        if doc_id in vector_results['ids'][0]:
            idx = vector_results['ids'][0].index(doc_id)
            document = vector_results['documents'][0][idx]
            vector_score = combined_scores[doc_id] / vector_weight if vector_weight > 0 else 0
        else:
            # If document is only in BM25 results, get it from MongoDB
            document = "Document not in vector results"  # You might want to fetch the actual document here
            vector_score = 0
        
        # Calculate BM25 score
        bm25_score = 0
        if doc_id in bm25_scores_dict:
            bm25_score = float(bm25_scores_dict[doc_id])  # Convert to float
            if score_range > 0:
                bm25_score = (bm25_score - min_score) / score_range
            else:
                bm25_score = 1.0 / len(bm25_scores)
        
        final_results.append({
            'id': doc_id,
            'document': document,
            'score': score,
            'vector_score': vector_score,
            'bm25_score': bm25_score
        })
    
    print("Search completed!")
    return final_results

def main():
    """Main function to run the application"""
    # Load environment and connect to MongoDB
    mongo_uri, db_name, collection_name = load_environment()
    client, collection = connect_mongodb(mongo_uri, db_name, collection_name)
    
    # Initialize ChromaDB and load model
    chroma_client, chroma_collection = initialize_chromadb()
    model = load_embedding_model()
    
    # Try to load existing BM25 index
    bm25, bm25_documents, bm25_ids = load_bm25_index()
    
    if bm25 is None:
        print("Creating new BM25 index...")
        bm25, bm25_documents, bm25_ids = process_documents(
            collection=collection,
            model=model,
            chroma_collection=chroma_collection,
            chroma_client=chroma_client
        )
    else:
        print(f"Successfully loaded existing BM25 index with {len(bm25_documents)} documents")
    
    # Example search
    query = "Lý lịch tư pháp cho người nước ngoài"
    print(f"\nPerforming search for query: {query}")
    results = hybrid_search(
        query_text=query,
        model=model,
        bm25=bm25,
        bm25_ids=bm25_ids,
        chroma_collection=chroma_collection
    )
    
    # Print results
    print("\nSearch Results:")
    for result in results:
        print(f"\nDocument: {result['document']}")
        print(f"Combined Score: {result['score']:.4f}")
        print(f"Vector Score: {result['vector_score']:.4f}")
        print(f"BM25 Score: {result['bm25_score']:.4f}")
        print("---")
    
    # Close MongoDB connection
    client.close()

if __name__ == "__main__":
    main()