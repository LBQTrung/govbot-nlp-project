from main import hybrid_search

results = hybrid_search("tìm thủ tục đăng ký kinh doanh")
for result in results:
    print(f"Document: {result['document']}")
    print(f"Combined Score: {result['score']:.4f}")
    print(f"Vector Score: {result['vector_score']:.4f}")
    print(f"BM25 Score: {result['bm25_score']:.4f}")
    print("---")