from flask import Blueprint, flash, redirect, render_template, request, url_for

from app.services.assessment_service import get_latest_assessment
from app.services.pipeline_service import (
    add_stage,
    create_pipeline_from_url,
    delete_pipeline,
    delete_stage,
    get_all_pipelines,
    get_pipeline,
    update_stage,
)
from app.services.recommendation_service import get_quick_wins

pipelines_bp = Blueprint("pipelines", __name__)


@pipelines_bp.route("/")
def list_pipelines():
    pipelines = get_all_pipelines()
    return render_template("pipelines/list.html", pipelines=pipelines)


@pipelines_bp.route("/new", methods=["GET", "POST"])
def new_pipeline():
    if request.method == "POST":
        repo_url = request.form.get("repository_url", "").strip()
        if not repo_url:
            flash("Repository URL is required.", "danger")
            return render_template("pipelines/new.html")
        pipeline = create_pipeline_from_url(repo_url)
        flash("Pipeline created.", "success")
        return redirect(url_for("pipelines.view_pipeline", pipeline_id=pipeline.id))
    return render_template("pipelines/new.html")


@pipelines_bp.route("/<int:pipeline_id>")
def view_pipeline(pipeline_id):
    pipeline = get_pipeline(pipeline_id)
    latest = get_latest_assessment(pipeline_id)
    quick_wins = get_quick_wins(latest) if latest else []
    return render_template(
        "pipelines/view.html",
        pipeline=pipeline,
        latest_assessment=latest,
        quick_wins=quick_wins,
    )


@pipelines_bp.route("/<int:pipeline_id>/stages", methods=["POST"])
def add_pipeline_stage(pipeline_id):
    get_pipeline(pipeline_id)
    add_stage(
        pipeline_id=pipeline_id,
        name=request.form["name"],
        tool=request.form.get("tool", ""),
        status=request.form.get("status", "unknown"),
        config_url=request.form.get("config_url", ""),
        notes=request.form.get("notes", ""),
    )
    flash("Stage added.", "success")
    return redirect(url_for("pipelines.view_pipeline", pipeline_id=pipeline_id))


@pipelines_bp.route("/<int:pipeline_id>/stages/<int:stage_id>/edit", methods=["POST"])
def edit_stage(pipeline_id, stage_id):
    update_stage(
        stage_id,
        name=request.form["name"],
        tool=request.form.get("tool", ""),
        status=request.form.get("status", "unknown"),
        config_url=request.form.get("config_url", ""),
        notes=request.form.get("notes", ""),
    )
    flash("Stage updated.", "success")
    return redirect(url_for("pipelines.view_pipeline", pipeline_id=pipeline_id))


@pipelines_bp.route("/<int:pipeline_id>/stages/<int:stage_id>/delete", methods=["POST"])
def remove_stage(pipeline_id, stage_id):
    delete_stage(stage_id)
    flash("Stage removed.", "success")
    return redirect(url_for("pipelines.view_pipeline", pipeline_id=pipeline_id))


@pipelines_bp.route("/<int:pipeline_id>/delete", methods=["POST"])
def remove_pipeline(pipeline_id):
    delete_pipeline(pipeline_id)
    flash("Pipeline removed.", "success")
    return redirect(url_for("pipelines.list_pipelines"))
