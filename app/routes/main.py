from flask import Blueprint, render_template

from app import db
from app.models import Pipeline
from app.models.pipeline import MATURITY_LEVELS
from app.services.recommendation_service import RECOMMENDATIONS
from config.assessment_questions import ASSESSMENT_DIMENSIONS

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    pipelines = db.session.scalars(db.select(Pipeline).order_by(Pipeline.name)).all()
    return render_template("index.html", pipelines=pipelines)


@main_bp.route("/reference")
def reference():
    return render_template(
        "reference.html",
        dimensions=ASSESSMENT_DIMENSIONS,
        maturity_levels=MATURITY_LEVELS,
        recommendations=RECOMMENDATIONS,
    )
