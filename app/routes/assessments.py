import io
import subprocess

from flask import Blueprint, render_template, request, redirect, url_for, flash, make_response

from app.services.assessment_service import (
    create_assessment_from_repo,
    get_assessment_history,
    get_latest_assessment,
    get_dimension_labels,
)
from app.services.recommendation_service import get_recommendations, get_quick_wins
from app.services.pipeline_service import get_pipeline
from config.assessment_questions import ASSESSMENT_DIMENSIONS

assessments_bp = Blueprint("assessments", __name__)


@assessments_bp.route("/pipelines/<int:pipeline_id>/assessments/new")
def new_assessment(pipeline_id):
    pipeline = get_pipeline(pipeline_id)
    if not pipeline.repository_url:
        flash("Set a repository URL on the pipeline before running an assessment.", "warning")
        return redirect(url_for("pipelines.view_pipeline", pipeline_id=pipeline_id))
    return render_template("assessments/new.html", pipeline=pipeline)


@assessments_bp.route("/pipelines/<int:pipeline_id>/assessments/", methods=["POST"])
def create(pipeline_id):
    pipeline = get_pipeline(pipeline_id)
    if not pipeline.repository_url:
        flash("Set a repository URL on the pipeline before running an assessment.", "warning")
        return redirect(url_for("pipelines.view_pipeline", pipeline_id=pipeline_id))

    try:
        assessment = create_assessment_from_repo(
            pipeline_id=pipeline.id,
            repo_url=pipeline.repository_url,
            assessed_by=request.form.get("assessed_by", ""),
        )
    except subprocess.CalledProcessError:
        flash("Failed to clone the repository. Check the URL is correct and accessible.", "danger")
        return redirect(url_for("assessments.new_assessment", pipeline_id=pipeline_id))
    except subprocess.TimeoutExpired:
        flash("Repository clone timed out. The repo may be too large or unreachable.", "danger")
        return redirect(url_for("assessments.new_assessment", pipeline_id=pipeline_id))

    flash("Assessment completed.", "success")
    return redirect(
        url_for("assessments.view_assessment", pipeline_id=pipeline.id, assessment_id=assessment.id)
    )


@assessments_bp.route("/pipelines/<int:pipeline_id>/assessments/<int:assessment_id>")
def view_assessment(pipeline_id, assessment_id):
    pipeline = get_pipeline(pipeline_id)
    from app.models import MaturityAssessment
    from app import db

    assessment = db.get_or_404(MaturityAssessment, assessment_id)
    dimension_labels = get_dimension_labels()
    dimensions = ASSESSMENT_DIMENSIONS
    recommendations = get_recommendations(assessment)
    quick_wins = get_quick_wins(assessment)

    previous = None
    history = get_assessment_history(pipeline_id)
    for i, a in enumerate(history):
        if a.id == assessment.id and i > 0:
            previous = history[i - 1]
            break

    return render_template(
        "assessments/view.html",
        pipeline=pipeline,
        assessment=assessment,
        dimensions=dimensions,
        dimension_labels=dimension_labels,
        recommendations=recommendations,
        quick_wins=quick_wins,
        previous=previous,
    )


@assessments_bp.route("/pipelines/<int:pipeline_id>/assessments/<int:assessment_id>/pdf")
def export_pdf(pipeline_id, assessment_id):
    from xhtml2pdf import pisa
    from app.models import MaturityAssessment
    from app import db

    pipeline = get_pipeline(pipeline_id)
    assessment = db.get_or_404(MaturityAssessment, assessment_id)
    dimensions = ASSESSMENT_DIMENSIONS
    recommendations = get_recommendations(assessment)
    quick_wins = get_quick_wins(assessment)

    html = render_template(
        "assessments/pdf.html",
        pipeline=pipeline,
        assessment=assessment,
        dimensions=dimensions,
        recommendations=recommendations,
        quick_wins=quick_wins,
    )

    pdf_buffer = io.BytesIO()
    pisa.CreatePDF(io.StringIO(html), dest=pdf_buffer)
    pdf_buffer.seek(0)

    response = make_response(pdf_buffer.read())
    filename = f"{pipeline.name}-assessment-{assessment.assessed_at.strftime('%Y%m%d')}.pdf"
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


@assessments_bp.route("/pipelines/<int:pipeline_id>/assessments/")
def history(pipeline_id):
    pipeline = get_pipeline(pipeline_id)
    assessments = get_assessment_history(pipeline_id)
    latest = get_latest_assessment(pipeline_id)
    return render_template(
        "assessments/history.html",
        pipeline=pipeline,
        assessments=assessments,
        latest=latest,
    )
