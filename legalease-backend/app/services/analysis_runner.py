from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models import Analysis, Document, RiskClause
from app.services.ai import analyze_with_ollama, validate_ai_result
from app.services.extractor import extract_text
from app.services.nlp import complexity_score


def run_analysis(analysis_id: int):
    db: Session = SessionLocal()
    try:
        analysis = db.get(Analysis, analysis_id)
        if not analysis:
            return
        document = db.get(Document, analysis.document_id)
        if not document:
            return
        analysis.status = "processing"
        document.status = "processing"
        db.commit()
        try:
            text = document.extracted_text.strip()
            if not text:
                text, _ = extract_text(document.file_path, document.filename)
                if not text.strip():
                    raise ValueError("No readable text could be extracted from the document")
                document.extracted_text = text
                db.commit()
            result = validate_ai_result(analyze_with_ollama(text))
            analysis.summary = result["summary"]
            analysis.simplified_text = result["simplified_text"]
            analysis.overall_risk = result["overall_risk"]
            analysis.risk_score = result["risk_score"]
            analysis.complexity_score = complexity_score(text)
            for clause in analysis.risk_clauses:
                db.delete(clause)
            db.flush()
            for item in result["risk_clauses"]:
                db.add(RiskClause(analysis_id=analysis.id, **item))
            analysis.status = "completed"
            analysis.error_message = None
            analysis.completed_at = datetime.now(timezone.utc)
            document.status = "completed"
            db.commit()
        except Exception as exc:
            db.rollback()
            analysis = db.get(Analysis, analysis_id)
            document = db.get(Document, analysis.document_id) if analysis else None
            if analysis:
                analysis.status = "failed"
                analysis.error_message = str(exc)[:2000]
                if document:
                    document.status = "failed"
                db.commit()
    finally:
        db.close()
