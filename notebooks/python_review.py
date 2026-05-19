# notebooks/python_review.py
# Week 1 Day 5 — Python fundamentals review for PolicyPulse

# --- LISTS ---
urls = ["https://example.com/policy1", "https://example.com/policy2"]

for url in urls:
    print(url)

urls.append("https://example.com/policy3")
print(len(urls))  # 3

# --- DICTIONARIES ---
document = {
    "title": "EU AI Act",
    "url": "https://eur-lex.europa.eu/ai-act",
    "jurisdiction": "EU",
    "published_at": "2024-03-13",
}

print(document["title"])

for key, value in document.items():
    print(f"{key}: {value}")

# --- LIST OF DICTS ---
documents = [
    {"title": "EU AI Act", "jurisdiction": "EU"},
    {"title": "US Executive Order on AI", "jurisdiction": "US"},
]

for doc in documents:
    print(doc["title"], "—", doc["jurisdiction"])


# --- FUNCTIONS ---
def clean_text(text):
    """Removes extra whitespace from text."""
    text = text.strip()
    text = text.replace("\n", " ")
    return text


dirty = "  EU AI Act regulation   "
clean = clean_text(dirty)
print(clean)


# --- TRY/EXCEPT ---
def safe_divide(a, b):
    try:
        return a / b
    except ZeroDivisionError as e:
        print(f"Error: {e}")
        return None


print(safe_divide(10, 2))
print(safe_divide(10, 0))
