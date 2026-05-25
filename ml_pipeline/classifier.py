# ml_pipeline/classifier.py
from transformers import pipeline

from infra.logger import get_logger

log = get_logger("ml_pipeline.classifier")


class PolicyClassifier:
    """
    Classifies policy documents by type, jurisdiction, and risk level.
    Uses zero-shot classification — no training data needed.
    """

    def __init__(self):
        log.info("Loading classification model...")
        self.classifier = pipeline(
            "zero-shot-classification",
            model="facebook/bart-large-mnli",
        )
        log.info("Model loaded.")

    def classify_doc_type(self, text: str) -> dict:
        labels = [
            "binding regulation",
            "policy guidance",
            "draft proposal",
            "research report",
            "news announcement",
            "technical standard",
        ]
        result = self.classifier(text[:1024], labels)
        return {
            "label": result["labels"][0],
            "score": round(result["scores"][0], 4),
        }

    def classify_jurisdiction(self, text: str) -> dict:
        labels = [
            "European Union policy",
            "United States policy",
            "United Kingdom policy",
            "United Arab Emirates or Gulf Cooperation Council policy",
            "Saudi Arabia policy",
        ]
        result = self.classifier(text[:1024], labels)
        label_map = {
            "European Union policy": "EU",
            "United States policy": "US",
            "United Kingdom policy": "UK",
            "United Arab Emirates or Gulf Cooperation Council policy": "UAE",
            "Saudi Arabia policy": "SA",
        }
        return {
            "label": label_map.get(result["labels"][0], "EU"),
            "score": round(result["scores"][0], 4),
        }

    def classify_risk_level(self, text: str) -> dict:
        labels = [
            "high risk — mandatory compliance with penalties",
            "medium risk — recommended compliance",
            "low risk — voluntary guidance",
        ]
        result = self.classifier(text[:1024], labels)
        label_map = {
            "high risk — mandatory compliance with penalties": "high",
            "medium risk — recommended compliance": "medium",
            "low risk — voluntary guidance": "low",
        }
        return {
            "level": label_map[result["labels"][0]],
            "score": round(result["scores"][0], 4),
        }

    def classify_full(self, text: str, title: str = "") -> dict:
        combined_text = f"{title}. {text}"[:1024]
        doc_type = self.classify_doc_type(combined_text)
        risk = self.classify_risk_level(combined_text)
        jurisdiction = self.classify_jurisdiction(combined_text)
        return {
            "doc_type": doc_type["label"],
            "doc_type_confidence": doc_type["score"],
            "risk_level": risk["level"],
            "risk_confidence": risk["score"],
            "jurisdiction": jurisdiction["label"],
            "jurisdiction_confidence": jurisdiction["score"],
        }
