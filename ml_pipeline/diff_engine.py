# ml_pipeline/diff_engine.py
import difflib


def compute_text_diff(old_text: str, new_text: str) -> dict:
    """
    Computes a structured diff between two versions of a document.
    Returns added lines, removed lines, and a change summary.
    """
    old_lines = [s.strip() for s in old_text.split(". ") if s.strip()]
    new_lines = [s.strip() for s in new_text.split(". ") if s.strip()]

    matcher = difflib.SequenceMatcher(None, old_lines, new_lines)

    added = []
    removed = []

    for opcode, i1, i2, j1, j2 in matcher.get_opcodes():
        if opcode == "insert":
            added.extend(new_lines[j1:j2])
        elif opcode == "delete":
            removed.extend(old_lines[i1:i2])
        elif opcode == "replace":
            removed.extend(old_lines[i1:i2])
            added.extend(new_lines[j1:j2])

    similarity = matcher.ratio()
    change_pct = round((1 - similarity) * 100, 1)

    return {
        "added": added[:10],
        "removed": removed[:10],
        "change_percent": change_pct,
        "is_major_change": change_pct > 20,
    }


def format_change_summary(diff: dict) -> str:
    """Plain-text summary of what changed."""
    parts = [f"Document changed by approximately {diff['change_percent']}%."]
    if diff["removed"]:
        parts.append("Removed: " + "; ".join(diff["removed"][:3]))
    if diff["added"]:
        parts.append("Added: " + "; ".join(diff["added"][:3]))
    if diff["is_major_change"]:
        parts.append("Flagged as major change (>20%).")
    return " ".join(parts)
