# tests/test_diff_engine.py
from ml_pipeline.diff_engine import compute_text_diff, format_change_summary


def test_compute_text_diff_detects_additions():
    old = "Section one. Section two."
    new = "Section one. Section two. Section three."
    diff = compute_text_diff(old, new)
    assert diff["change_percent"] >= 0
    assert len(diff["added"]) >= 1


def test_major_change_flag_when_large_edit():
    old = "Alpha. Beta. Gamma."
    new = "Completely different content. New policy scope."
    diff = compute_text_diff(old, new)
    assert diff["is_major_change"] is True


def test_format_change_summary_includes_percent():
    diff = {"change_percent": 25.0, "added": ["new clause"], "removed": [], "is_major_change": True}
    summary = format_change_summary(diff)
    assert "25" in summary
    assert "major change" in summary.lower()
