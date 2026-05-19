-- Week 5: speed up semantic search (cosine distance)
CREATE INDEX IF NOT EXISTS idx_documents_embedding_hnsw
ON documents
USING hnsw (embedding vector_cosine_ops);
