from app import db
from app.models.pipeline import MaturityAssessment, DimensionResponse
from app.services.git_analyzer import GitAnalyzer
from config.assessment_questions import ASSESSMENT_DIMENSIONS


def get_dimension_labels():
    return {key: dim["label"] for key, dim in ASSESSMENT_DIMENSIONS.items()}


def create_assessment_from_repo(pipeline_id, repo_url, assessed_by=None):
    """Clone a git repo, analyze it for evidence, and create a scored assessment."""
    analyzer = GitAnalyzer(repo_url)
    results = analyzer.analyze()

    dimension_scores = {dim: data["score"] for dim, data in results.items()}
    valid_scores = [s for s in dimension_scores.values() if s]
    overall = round(sum(valid_scores) / len(valid_scores)) if valid_scores else 0

    assessment = MaturityAssessment(
        pipeline_id=pipeline_id,
        assessed_by=assessed_by,
        overall_score=overall,
        version_control_score=dimension_scores.get("version_control", 0),
        build_process_score=dimension_scores.get("build_process", 0),
        testing_score=dimension_scores.get("testing", 0),
        deployment_score=dimension_scores.get("deployment", 0),
        monitoring_score=dimension_scores.get("monitoring", 0),
        security_score=dimension_scores.get("security", 0),
        configuration_management_score=dimension_scores.get("configuration_management", 0),
        feedback_loops_score=dimension_scores.get("feedback_loops", 0),
    )
    db.session.add(assessment)
    db.session.flush()

    for dim, data in results.items():
        for ev in data["evidence"]:
            response = DimensionResponse(
                assessment_id=assessment.id,
                dimension=dim,
                question_key=ev["check"],
                score=1 if ev["found"] else 0,
                notes=ev["detail"],
            )
            db.session.add(response)

    db.session.commit()
    return assessment


def get_assessment_history(pipeline_id):
    return db.session.scalars(
        db.select(MaturityAssessment)
        .filter_by(pipeline_id=pipeline_id)
        .order_by(MaturityAssessment.assessed_at.asc())
    ).all()


def get_latest_assessment(pipeline_id):
    return db.session.scalars(
        db.select(MaturityAssessment)
        .filter_by(pipeline_id=pipeline_id)
        .order_by(MaturityAssessment.assessed_at.desc())
        .limit(1)
    ).first()
