# ml_pipeline/classify_explore.py — Week 4 Day 22
from transformers import pipeline


def main():
    classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

    text = """
    The AI Act establishes obligations for providers and deployers of AI systems
    in the European Union. High-risk AI systems must comply with data governance
    requirements and register in the EU database before being placed on the market.
    """

    candidate_labels = [
        "regulation",
        "guidance",
        "policy draft",
        "research paper",
        "news",
    ]

    result = classifier(text, candidate_labels)

    print("Document type:", result["labels"][0])
    print("Confidence:", round(result["scores"][0], 3))
    print()
    print("All scores:")
    for label, score in zip(result["labels"], result["scores"]):
        print(f"  {label}: {round(score, 3)}")


if __name__ == "__main__":
    main()
