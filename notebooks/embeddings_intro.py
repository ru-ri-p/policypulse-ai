# notebooks/embeddings_intro.py — Week 5 Day 29
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


def main():
    model = SentenceTransformer("all-MiniLM-L6-v2")

    sentences = [
        "The EU AI Act regulates high-risk artificial intelligence systems.",
        "European regulations on machine learning impose strict requirements.",
        "The best recipe for chocolate cake uses dark cocoa powder.",
    ]

    embeddings = model.encode(sentences)
    print("Shape:", embeddings.shape)

    sim_12 = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
    sim_13 = cosine_similarity([embeddings[0]], [embeddings[2]])[0][0]

    print(f"Similarity (EU Act vs ML regulations): {sim_12:.3f}")
    print(f"Similarity (EU Act vs chocolate cake): {sim_13:.3f}")


if __name__ == "__main__":
    main()
