from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors
from reportlab.lib.units import mm
from app.core.config import get_settings


def generate_report(document, analysis) -> str:
    settings = get_settings()
    Path(settings.report_dir).mkdir(parents=True, exist_ok=True)
    output = Path(settings.report_dir) / f"document-{document.id}-legalease-report.pdf"
    styles = getSampleStyleSheet()
    title = ParagraphStyle("Title2", parent=styles["Title"], alignment=TA_CENTER, spaceAfter=12)
    body = ParagraphStyle("Body2", parent=styles["BodyText"], leading=15, spaceAfter=8)
    small = ParagraphStyle("Small", parent=body, fontSize=8.5, leading=11)

    story = [Paragraph("LegalEase Analysis Report", title), Paragraph(document.filename, styles["Heading2"]), Spacer(1, 5)]
    story.append(Table([
        ["Overall Risk", analysis.overall_risk],
        ["Risk Score", f"{analysis.risk_score if analysis.risk_score is not None else '—'}/100"],
        ["Complexity", f"{analysis.complexity_score if analysis.complexity_score is not None else '—'}/100"],
    ], colWidths=[45*mm, 125*mm], style=TableStyle([
        ("GRID", (0,0), (-1,-1), 0.5, colors.grey), ("BACKGROUND", (0,0), (0,-1), colors.whitesmoke),
        ("VALIGN", (0,0), (-1,-1), "TOP"), ("FONTNAME", (0,0), (0,-1), "Helvetica-Bold"),
        ("PADDING", (0,0), (-1,-1), 6),
    ])))
    story += [Spacer(1, 12), Paragraph("Executive Summary", styles["Heading2"]), Paragraph((analysis.summary or "No summary returned.").replace("\n", "<br/>"), body)]
    story += [Paragraph("Risk Analysis", styles["Heading2"])]
    if analysis.risk_clauses:
        for risk in analysis.risk_clauses:
            story += [Paragraph(f"{risk.title} — {risk.risk_level}", styles["Heading3"]), Paragraph(f"<b>Clause:</b> {risk.clause_text}", small), Paragraph(f"<b>Why it matters:</b> {risk.explanation}", body), Paragraph(f"<b>Recommendation:</b> {risk.recommendation}", body), Spacer(1, 4)]
    else:
        story.append(Paragraph("No risk clauses were returned by the AI analysis.", body))
    story += [PageBreak(), Paragraph("Simplified Document", styles["Heading2"]), Paragraph((analysis.simplified_text or "No simplified text returned.").replace("\n", "<br/>"), body)]
    story += [Spacer(1, 15), Paragraph("LegalEase provides AI-generated explanations for informational purposes and does not replace professional legal advice.", small)]
    SimpleDocTemplate(str(output), pagesize=A4, rightMargin=18*mm, leftMargin=18*mm, topMargin=18*mm, bottomMargin=18*mm).build(story)
    return str(output)
