# ml_pipeline/summariser.py
from transformers import pipeline

from infra.logger import get_logger

log = get_logger("ml_pipeline.summariser")


class PolicySummariser:
    def __init__(self):
        log.info("Loading summarisation model...")
        self.summariser = pipeline(
            "summarization",
            model="facebook/bart-large-cnn",
            max_length=200,
            min_length=50,
            do_sample=False,
        )
        log.info("Summarisation model loaded.")

    def summarise(self, text: str) -> str:
        truncated = " ".join(text.split()[:900])
        if len(truncated.split()) < 50:
            return text
        result = self.summariser(truncated)
        return result[0]["summary_text"]
