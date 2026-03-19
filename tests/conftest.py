import pytest

from app import create_app, db as _db
from app.models import Pipeline, MaturityAssessment


@pytest.fixture
def app():
    app = create_app("testing")
    with app.app_context():
        _db.create_all()
        yield app
        _db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def db(app):
    return _db


@pytest.fixture
def sample_pipeline(app, db):
    pipeline = Pipeline(name="Test Pipeline", description="A test pipeline", team="Platform")
    db.session.add(pipeline)
    db.session.commit()
    return pipeline


@pytest.fixture
def sample_assessment(app, db, sample_pipeline):
    assessment = MaturityAssessment(
        pipeline_id=sample_pipeline.id,
        assessed_by="tester",
        overall_score=3,
        version_control_score=3,
        build_process_score=4,
        testing_score=2,
        deployment_score=3,
        monitoring_score=3,
        security_score=2,
        configuration_management_score=3,
        feedback_loops_score=4,
    )
    db.session.add(assessment)
    db.session.commit()
    return assessment
