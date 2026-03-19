from app.services.pipeline_service import (
    get_all_pipelines,
    get_pipeline,
    create_pipeline_from_url,
    delete_pipeline,
    extract_team_from_url,
    extract_name_from_url,
    add_stage,
    update_stage,
    delete_stage,
)


def test_create_pipeline_from_url(app, db):
    pipeline = create_pipeline_from_url("https://github.com/myorg/my-service.git")
    assert pipeline.id is not None
    assert pipeline.name == "my-service"
    assert pipeline.team == "myorg"
    assert pipeline.repository_url == "https://github.com/myorg/my-service.git"


def test_get_all_pipelines(app, db, sample_pipeline):
    pipelines = get_all_pipelines()
    assert len(pipelines) == 1
    assert pipelines[0].name == "Test Pipeline"


def test_get_pipeline(app, db, sample_pipeline):
    pipeline = get_pipeline(sample_pipeline.id)
    assert pipeline.name == "Test Pipeline"


def test_add_stage(app, db, sample_pipeline):
    stage = add_stage(sample_pipeline.id, "build", tool="Jenkins", status="healthy")
    assert stage.id is not None
    assert stage.name == "build"
    assert stage.tool == "Jenkins"


def test_update_stage(app, db, sample_pipeline):
    stage = add_stage(sample_pipeline.id, "test", tool="pytest")
    updated = update_stage(stage.id, tool="jest", status="healthy")
    assert updated.tool == "jest"
    assert updated.status == "healthy"


def test_delete_stage(app, db, sample_pipeline):
    stage = add_stage(sample_pipeline.id, "deploy", tool="ArgoCD")
    stage_id = stage.id
    delete_stage(stage_id)
    from app.models import PipelineStage
    assert db.session.get(PipelineStage, stage_id) is None


def test_delete_pipeline(app, db, sample_pipeline):
    pipeline_id = sample_pipeline.id
    delete_pipeline(pipeline_id)
    from app.models import Pipeline
    assert db.session.get(Pipeline, pipeline_id) is None


def test_extract_team_from_https_url():
    assert extract_team_from_url("https://github.com/myorg/myrepo.git") == "myorg"
    assert extract_team_from_url("https://github.com/myorg/myrepo") == "myorg"
    assert extract_team_from_url("https://gitlab.com/group/subgroup/repo") == "group"


def test_extract_team_from_ssh_url():
    assert extract_team_from_url("git@github.com:myorg/myrepo.git") == "myorg"
    assert extract_team_from_url("git@gitlab.com:team/project.git") == "team"


def test_extract_team_empty_url():
    assert extract_team_from_url("") == ""
    assert extract_team_from_url(None) == ""


def test_extract_name_from_https_url():
    assert extract_name_from_url("https://github.com/org/my-repo.git") == "my-repo"
    assert extract_name_from_url("https://github.com/org/my-repo") == "my-repo"


def test_extract_name_from_ssh_url():
    assert extract_name_from_url("git@github.com:org/my-repo.git") == "my-repo"


def test_extract_name_empty_url():
    assert extract_name_from_url("") == ""
    assert extract_name_from_url(None) == ""
