from datetime import datetime, timezone

from app import db

MATURITY_LEVELS = {
    1: "Regressive",
    2: "Repeatable",
    3: "Consistent",
    4: "Quantitatively Managed",
    5: "Optimizing",
}


class Pipeline(db.Model):
    __tablename__ = "pipelines"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    repository_url = db.Column(db.String(500))
    team = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    stages = db.relationship("PipelineStage", backref="pipeline", lazy=True, cascade="all, delete-orphan")
    assessments = db.relationship("MaturityAssessment", backref="pipeline", lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Pipeline {self.name}>"


class PipelineStage(db.Model):
    __tablename__ = "pipeline_stages"

    id = db.Column(db.Integer, primary_key=True)
    pipeline_id = db.Column(db.Integer, db.ForeignKey("pipelines.id"), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    tool = db.Column(db.String(200))
    status = db.Column(db.String(50), default="unknown")
    config_url = db.Column(db.String(500))
    notes = db.Column(db.Text)

    def __repr__(self):
        return f"<PipelineStage {self.name} ({self.tool})>"


class MaturityAssessment(db.Model):
    __tablename__ = "maturity_assessments"

    id = db.Column(db.Integer, primary_key=True)
    pipeline_id = db.Column(db.Integer, db.ForeignKey("pipelines.id"), nullable=False)
    assessed_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    assessed_by = db.Column(db.String(200))
    overall_score = db.Column(db.Integer)

    # Scores per dimension (1-5)
    version_control_score = db.Column(db.Integer)
    build_process_score = db.Column(db.Integer)
    testing_score = db.Column(db.Integer)
    deployment_score = db.Column(db.Integer)
    monitoring_score = db.Column(db.Integer)
    security_score = db.Column(db.Integer)
    configuration_management_score = db.Column(db.Integer)
    feedback_loops_score = db.Column(db.Integer)
    ai_readiness_score = db.Column(db.Integer)

    application_type = db.Column(db.String(50))
    application_type_label = db.Column(db.String(100))
    classification_confidence = db.Column(db.Integer)

    notes = db.Column(db.Text)

    responses = db.relationship("DimensionResponse", backref="assessment", lazy=True, cascade="all, delete-orphan")

    DIMENSIONS = [
        "version_control", "build_process", "testing", "deployment",
        "monitoring", "security", "configuration_management", "feedback_loops",
        "ai_readiness",
    ]

    @property
    def dimension_scores(self):
        return {d: getattr(self, f"{d}_score") for d in self.DIMENSIONS}

    @property
    def maturity_label(self):
        if self.overall_score:
            return MATURITY_LEVELS.get(self.overall_score, "Unknown")
        return "Not assessed"

    def __repr__(self):
        return f"<MaturityAssessment pipeline={self.pipeline_id} score={self.overall_score}>"


class DimensionResponse(db.Model):
    __tablename__ = "dimension_responses"

    id = db.Column(db.Integer, primary_key=True)
    assessment_id = db.Column(db.Integer, db.ForeignKey("maturity_assessments.id"), nullable=False)
    dimension = db.Column(db.String(50), nullable=False)
    question_key = db.Column(db.String(100), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    notes = db.Column(db.Text)

    def __repr__(self):
        return f"<DimensionResponse {self.dimension}.{self.question_key}={self.score}>"
