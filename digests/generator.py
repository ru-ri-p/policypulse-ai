# digests/generator.py
import json
import os

from dotenv import load_dotenv
from openai import OpenAI

from infra.logger import get_logger

load_dotenv()
log = get_logger("digests.generator")

DIGEST_PROMPT = """
You are a regulatory compliance assistant specialising in AI governance for organisations operating in the UAE/GCC region. Analyse this AI policy document and summarise its impact for companies headquartered in Dubai or operating across the GCC, including any extraterritorial obligations (e.g. EU AI Act exposure).

Respond with ONLY a JSON object in this exact format:
{{
  "what_changed": "One sentence: what this document says or requires.",
  "who_is_affected": "One sentence: which companies, sectors, or roles in the UAE/GCC this applies to.",
  "what_to_do": "One sentence: the most important action compliance teams should take.",
  "urgency": "immediate | within_6_months | informational",
  "key_deadline": "date string or null"
}}

Document title: {title}
Document text (excerpt):
{content}
"""

FALLBACK_DIGEST = {
    "what_changed": "Digest unavailable.",
    "who_is_affected": "",
    "what_to_do": "",
    "urgency": "informational",
    "key_deadline": None,
}


def _get_client() -> OpenAI | None:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key.startswith("sk-your"):
        return None
    return OpenAI(api_key=api_key)


def generate_digest(title: str, content: str) -> dict:
    """
    Calls GPT-4o-mini to generate a structured compliance digest.
    Returns a dict with the 5 digest fields.
    """
    content_excerpt = " ".join((content or "").split()[:2000])
    prompt = DIGEST_PROMPT.format(title=title or "Untitled", content=content_excerpt)

    client = _get_client()
    if client is None:
        log.warning("OPENAI_API_KEY not set — returning fallback digest")
        return dict(FALLBACK_DIGEST)

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.1,
            max_tokens=400,
        )
        return json.loads(response.choices[0].message.content)
    except Exception as exc:
        log.error("Digest generation failed: %s", exc)
        return dict(FALLBACK_DIGEST)
