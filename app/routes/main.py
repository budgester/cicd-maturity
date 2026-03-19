from flask import Blueprint, render_template

from app import db
from app.models import Pipeline

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    pipelines = db.session.scalars(db.select(Pipeline).order_by(Pipeline.name)).all()
    return render_template("index.html", pipelines=pipelines)
