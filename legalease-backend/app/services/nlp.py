import re
import spacy
from nltk.tokenize import wordpunct_tokenize

LEGAL_TERMS = {
    "indemnify", "indemnification", "liability", "liable", "termination", "renewal",
    "penalty", "damages", "arbitration", "jurisdiction", "confidentiality", "non-compete",
    "privacy", "personal data", "fee", "fees", "charge", "default", "breach", "warranty",
    "disclaimer", "intellectual property", "governing law", "notice", "auto-renewal",
}

try:
    NLP = spacy.load("en_core_web_sm")
except Exception:
    NLP = spacy.blank("en")
    NLP.add_pipe("sentencizer")


def preprocess_text(text: str) -> dict:
    cleaned = re.sub(r"\s+", " ", text).strip()
    doc = NLP(cleaned)
    sentences = [s.text.strip() for s in doc.sents if s.text.strip()]
    tokens = wordpunct_tokenize(cleaned)
    return {"cleaned_text": cleaned, "sentences": sentences, "token_count": len(tokens)}


def complexity_score(text: str) -> int:
    data = preprocess_text(text)
    sentences = data["sentences"] or [text]
    words = [w for w in wordpunct_tokenize(text) if re.search(r"[A-Za-z]", w)]
    avg_sentence = len(words) / max(len(sentences), 1)
    legal_hits = sum(1 for term in LEGAL_TERMS if re.search(rf"\b{re.escape(term)}\b", text, re.I))
    long_sentences = sum(1 for s in sentences if len(wordpunct_tokenize(s)) > 35)
    score = 20 + min(avg_sentence * 0.8, 40) + min(legal_hits * 2, 20) + min(long_sentences * 2, 20)
    return max(0, min(100, round(score)))
