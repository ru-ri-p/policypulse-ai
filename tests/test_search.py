# tests/test_search.py
from unittest.mock import MagicMock, patch


@patch("ml_pipeline.search.get_connection")
@patch("ml_pipeline.search._get_embedder")
def test_semantic_search_returns_rows(mock_embedder, mock_conn):
    mock_embedder.return_value.embed_text.return_value = [0.1, 0.2, 0.3]

    cursor = MagicMock()
    cursor.fetchall.return_value = [
        (42, "AI Act summary", "EU", 0.87),
        (7, "NIST framework", "US", 0.75),
    ]
    conn = MagicMock()
    conn.cursor.return_value = cursor
    mock_conn.return_value = conn

    from ml_pipeline.search import semantic_search

    results = semantic_search("facial recognition EU", limit=5)
    assert len(results) == 2
    assert results[0][0] == 42
    cursor.execute.assert_called_once()


@patch("ml_pipeline.search._get_embedder")
def test_semantic_search_passes_limit_to_query(mock_embedder):
    mock_embedder.return_value.embed_text.return_value = [0.0] * 384

    with patch("ml_pipeline.search.get_connection") as mock_conn:
        cursor = MagicMock()
        cursor.fetchall.return_value = []
        conn = MagicMock()
        conn.cursor.return_value = cursor
        mock_conn.return_value = conn

        from ml_pipeline.search import semantic_search

        semantic_search("test query", limit=3)
        args = cursor.execute.call_args[0][1]
        assert args[-1] == 3
