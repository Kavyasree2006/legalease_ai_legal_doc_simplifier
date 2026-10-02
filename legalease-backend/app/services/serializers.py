def user_dict(user):
    return {"id": user.id, "name": user.name, "email": user.email, "created_at": user.created_at.isoformat() if user.created_at else None}


def risk_dict(r):
    return {
        "id": r.id,
        "title": r.title,
        "clause_text": r.clause_text,
        "risk_type": r.risk_type,
        "risk_level": r.risk_level,
        "explanation": r.explanation,
        "recommendation": r.recommendation,
    }


def analysis_dict(a):
    return {
        "id": a.id,
        "analysis_id": a.id,
        "document_id": a.document_id,
        "status": a.status,
        "summary": a.summary,
        "executive_summary": a.summary,
        "simplified_text": a.simplified_text,
        "overall_risk": a.overall_risk,
        "risk_score": a.risk_score,
        "complexity_score": a.complexity_score,
        "error_message": a.error_message,
        "created_at": a.created_at.isoformat() if a.created_at else None,
        "completed_at": a.completed_at.isoformat() if a.completed_at else None,
        "risk_clauses": [risk_dict(r) for r in a.risk_clauses],
    }


def document_dict(d, include_text=False):
    latest = max(d.analyses, key=lambda a: a.id, default=None)
    data = {
        "id": d.id,
        "document_id": d.id,
        "filename": d.filename,
        "file_type": d.file_type,
        "file_size": d.file_size,
        "size": d.file_size,
        "status": d.status,
        "created_at": d.created_at.isoformat() if d.created_at else None,
        "upload_date": d.created_at.isoformat() if d.created_at else None,
    }
    if latest:
        data.update({
            "analysis_id": latest.id,
            "overall_risk": latest.overall_risk,
            "risk_level": latest.overall_risk,
            "risk_score": latest.risk_score,
            "complexity_score": latest.complexity_score,
            "analysis_status": latest.status,
        })
    if include_text:
        data["extracted_text"] = d.extracted_text
    return data
