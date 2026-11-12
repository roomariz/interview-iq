import json
from statistics import mean
from typing import Optional

from interview_app_backend.models.report import Report

try:
    from fpdf2 import FPDF

    FPDF_AVAILABLE = True
except ImportError:
    FPDF_AVAILABLE = False


def summarise_performance(session_data: dict) -> dict:
    scores = session_data.get("scores", [])
    breakdown = {
        dimension: round(mean([entry[dimension] for entry in scores]), 1)
        for dimension in ("technical_accuracy", "clarity", "structure", "relevance")
        if scores and all(dimension in entry for entry in scores)
    }
    overall_average = round(mean(breakdown.values()), 1) if breakdown else 0.0
    questions_completed = session_data.get("completed_questions", len(scores))
    duration_minutes = session_data.get("duration_minutes", 0)
    readiness = "Needs Improvement" if overall_average < 7 else "Good"
    return {
        "title": "Interview Session Complete!",
        "overall_performance": f"{int(round(overall_average * 10))}% ({readiness})",
        "questions_completed": questions_completed,
        "session_duration": f"{duration_minutes} minutes",
        "average_scores": breakdown,
        "strengths": session_data.get("strengths", []),
        "improvement_areas": session_data.get("improvement_areas", []),
        "focus_areas": session_data.get("focus_areas", []),
        "recommended_next_steps": [
            "Practice STAR framework (Situation, Task, Action, Result)",
            "Prepare specific metrics for key projects",
            "Practice follow-up questions on technical trade-offs",
            "Try again at HARD difficulty level",
        ],
    }


def build_report(session_summary: dict) -> Report:
    content = json.dumps(session_summary, indent=2, ensure_ascii=True)
    return Report(
        title="Interview Session Report",
        content=content,
        filename="interview-session-report.json",
        sections=["summary", "scores", "strengths", "improvement_areas"],
    )


def build_pdf_report(session_summary: dict) -> Optional[Report]:
    if not FPDF_AVAILABLE:
        return None

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", size=16)
    pdf.cell(200, 10, txt=session_summary.get("title", "Interview Session Report"), align="C")
    pdf.ln(15)

    pdf.set_font(size=12)
    pdf.cell(200, 8, txt=f"Performance: {session_summary.get('overall_performance', 'N/A')}", ln=True)
    pdf.cell(200, 8, txt=f"Questions Completed: {session_summary.get('questions_completed', 0)}", ln=True)
    pdf.cell(200, 8, txt=f"Session Duration: {session_summary.get('session_duration', '0 minutes')}", ln=True)
    pdf.ln(10)

    pdf.set_font(size=14)
    pdf.cell(200, 10, txt="Score Breakdown", ln=True)
    pdf.set_font(size=11)
    for dim, score in session_summary.get("average_scores", {}).items():
        pdf.cell(200, 7, txt=f"{dim.replace('_', ' ').title()}: {score}/10", ln=True)
    pdf.ln(10)

    strengths = session_summary.get("strengths", [])
    if strengths:
        pdf.set_font(size=14)
        pdf.cell(200, 10, txt="Strengths", ln=True)
        pdf.set_font(size=11)
        for strength in strengths[:5]:
            pdf.cell(200, 7, txt=f"  - {strength}", ln=True)
        pdf.ln(5)

    improvements = session_summary.get("improvement_areas", [])
    if improvements:
        pdf.set_font(size=14)
        pdf.cell(200, 10, txt="Improvement Areas", ln=True)
        pdf.set_font(size=11)
        for imp in improvements[:5]:
            pdf.cell(200, 7, txt=f"  - {imp}", ln=True)
        pdf.ln(10)

    next_steps = session_summary.get("recommended_next_steps", [])
    if next_steps:
        pdf.set_font(size=14)
        pdf.cell(200, 10, txt="Recommended Next Steps", ln=True)
        pdf.set_font(size=11)
        for step in next_steps[:3]:
            pdf.cell(200, 7, txt=f"  - {step}", ln=True)

    content = pdf.output(dest="S").encode("latin-1")
    return Report(
        title="Interview Session Report",
        content=content,
        filename="interview-session-report.pdf",
        mime_type="application/pdf",
    )
