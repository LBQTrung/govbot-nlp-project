import numpy as np
import pickle
import chromadb
import os
from pyvi.ViTokenizer import tokenize
from sklearn.preprocessing import minmax_scale
from sentence_transformers import SentenceTransformer
from app.retriever_services.filter import filter_procedures_with_gemini

# Lấy đường dẫn tuyệt đối đến thư mục chứa file retriever.py
current_dir = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(current_dir, 'vietnamese-embedding')

embedding_model = SentenceTransformer(model_path)

# Sử dụng đường dẫn tuyệt đối cho chroma_db và bm25
chroma_db_path = os.path.join(current_dir, 'chroma_db')
bm25_path = os.path.join(current_dir, 'bm25')

chroma_client = chromadb.PersistentClient(path=chroma_db_path)
chroma_collection = chroma_client.get_or_create_collection(
    name="procedure_collection",
    metadata={"hnsw:space": "cosine"}
)

with open(os.path.join(bm25_path, 'bm25.pkl'), 'rb') as f:
    bm25 = pickle.load(f)
with open(os.path.join(bm25_path, 'documents_names.pkl'), 'rb') as f:
    documents_names = pickle.load(f)
with open(os.path.join(bm25_path, 'documents_ids.pkl'), 'rb') as f:
    documents_ids = pickle.load(f)


def hybrid_search(query, alpha=0.5, top_k=10):
    # BM25
    tokenized_query = tokenize(query.lower())
    bm25_scores = bm25.get_scores(tokenized_query)
    bm25_norm = minmax_scale(bm25_scores).tolist()
    
    # Embedding search từ Chroma
    embedding = embedding_model.encode([query])[0].tolist()
    chroma_result = chroma_collection.query(query_embeddings=[embedding], n_results=297)
    
    # Trích xuất điểm embedding từ Chroma
    retrieved_ids = chroma_result['ids'][0]
    emb_scores = chroma_result['distances'][0]
    emb_similarities = [1 - d for d in emb_scores]
    emb_norm = minmax_scale(emb_similarities).tolist()

    idx_to_emb_norm = {retrieved_ids[i]: emb_norm[i] for i in range(len(retrieved_ids))}

    final_scores = []

    for index in range(297):
        bm25_score = bm25_norm[index]
        embeding_score = idx_to_emb_norm[str(index)]
        final_score = alpha * bm25_score + (1 - alpha) * embeding_score
        final_scores.append(final_score)

    ranked_indices = np.argsort(final_scores)[::-1]
    for i in range(top_k):
        print(f"Rank#{i+1} with score {final_scores[ranked_indices[i]]}: {documents_names[ranked_indices[i]]}")

    return {documents_ids[ranked_indices[i]]: documents_names[ranked_indices[i]] for i in range(top_k)}


def retrieve_procedures(query, db, top_k=20):
    # 1. Hybrid search
    hybrid_results = hybrid_search(query, top_k=top_k)

    # 2. Filter procedures with Gemini
    filtered_procedures = filter_procedures_with_gemini(query, db, hybrid_results)

    return filtered_procedures

