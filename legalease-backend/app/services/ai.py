import json
import re
import httpx
from app.core.config import get_settings

SYSTEM_PROMPT = """You are LegalEase, an AI system that explains legal documents for ordinary users.
You are not a lawyer and must not claim to provide legal advice. Preserve the meaning of the source.
Identify potentially risky clauses, explain why they matter, and provide informational recommendations.
Return ONLY valid JSON matching the requested schema. Do not use markdown fences."""


def _extract_json(text: str) -> dict:
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.S)
        if not match:
            raise ValueError("LLM returned invalid JSON")
        return json.loads(match.group(0))


def analyze_with_ollama(text: str) -> dict:
    settings = get_settings()
    # Keep prompts bounded enough for a local model. The complete source remains stored in PostgreSQL.
    source = text[:50000]
    schema = {
        "summary": "string",
        "simplified_text": "string",
        "overall_risk": "LOW|MEDIUM|HIGH",
        "risk_score": "integer 0-100",
        "risk_clauses": [
            {
                "title": "string",
                "risk_type": "string",
                "clause_text": "short exact or near-exact source excerpt",
                "risk_level": "LOW|MEDIUM|HIGH",
                "explanation": "string",
                "recommendation": "string"
            }
        ]
    }
    prompt = f"""{SYSTEM_PROMPT}

Analyze this legal document.

Required JSON schema:
{json.dumps(schema, indent=2)}

Rules:
- summary: concise executive summary covering purpose, parties/roles if stated, obligations, financial terms, restrictions, termination and important risks.
- simplified_text: plain-English explanation of the document, preserving important conditions.
- risk_clauses: include only clauses actually supported by the source. Look especially for hidden fees, auto-renewal, liability/indemnity, penalties, privacy/data use, termination restrictions, broad permissions, and dispute clauses.
- risk_score is an overall informational risk indicator, not legal advice.
- Use LOW, MEDIUM, or HIGH exactly.

DOCUMENT:
{source}
"""
    url = settings.ollama_base_url.rstrip("/") + "/api/generate"
    response = httpx.post(url, json={"model": settings.ollama_model, "prompt": prompt, "stream": False, "format": "json"}, timeout=300)
    response.raise_for_status()
    payload = response.json()
    raw = payload.get("response", "")
    result = _extract_json(raw)
    if not isinstance(result, dict):
        raise ValueError("LLM response must be a JSON object")
    return result


def validate_ai_result(result: dict) -> dict:
    risk = str(result.get("overall_risk", "UNKNOWN")).upper()
    if risk not in {"LOW", "MEDIUM", "HIGH"}:
        risk = "MEDIUM"
    try:
        score = max(0, min(100, int(result.get("risk_score", 0))))
    except (TypeError, ValueError):
        score = 0
    clauses = result.get("risk_clauses") or []
    cleaned = []
    for c in clauses:
        if not isinstance(c, dict):
            continue
        level = str(c.get("risk_level", "MEDIUM")).upper()
        if level not in {"LOW", "MEDIUM", "HIGH"}:
            level = "MEDIUM"
        cleaned.append({
            "title": str(c.get("title") or c.get("risk_type") or "Potential risk")[:160],
            "risk_type": str(c.get("risk_type") or "General")[:100],
            "clause_text": str(c.get("clause_text") or "")[:10000],
            "risk_level": level,
            "explanation": str(c.get("explanation") or ""),
            "recommendation": str(c.get("recommendation") or ""),
        })
    return {
        "summary": str(result.get("summary") or ""),
        "simplified_text": str(result.get("simplified_text") or ""),
        "overall_risk": risk,
        "risk_score": score,
        "risk_clauses": cleaned,
    }
