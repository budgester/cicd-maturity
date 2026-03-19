import subprocess

from app.services.assessment_service import (
    create_assessment_from_repo,
    get_assessment_history,
    get_latest_assessment,
)


def _make_test_repo(tmp_path):
    """Create a minimal git repo with some files for testing."""
    repo = tmp_path / "test-repo"
    repo.mkdir()
    (repo / "README.md").write_text("# Test Project\n")
    (repo / ".gitignore").write_text("*.pyc\n__pycache__/\n.env\n")
    (repo / "requirements.txt").write_text("flask>=3.0\npytest>=8.0\n")

    tests_dir = repo / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_example.py").write_text("def test_example():\n    assert True\n")

    config_dir = repo / "config"
    config_dir.mkdir()
    (config_dir / "settings.py").write_text("DEBUG = True\n")

    (repo / ".env.example").write_text("SECRET_KEY=changeme\n")

    subprocess.run(["git", "init", str(repo)], capture_output=True, check=True)
    subprocess.run(["git", "add", "."], cwd=repo, capture_output=True, check=True)
    subprocess.run(
        ["git", "commit", "-m", "feat: initial project setup"],
        cwd=repo, capture_output=True, check=True,
        env={"GIT_AUTHOR_NAME": "Test", "GIT_AUTHOR_EMAIL": "t@t.com",
             "GIT_COMMITTER_NAME": "Test", "GIT_COMMITTER_EMAIL": "t@t.com",
             "HOME": str(tmp_path), "PATH": "/usr/bin:/bin:/usr/local/bin"},
    )
    return str(repo)


def test_create_assessment_from_repo(app, db, sample_pipeline, tmp_path):
    repo_path = _make_test_repo(tmp_path)
    assessment = create_assessment_from_repo(sample_pipeline.id, repo_path, "tester")

    assert assessment.id is not None
    assert assessment.overall_score >= 1
    assert assessment.assessed_by == "tester"
    assert assessment.version_control_score >= 1
    assert assessment.testing_score >= 1
    assert len(assessment.responses) > 0


def test_evidence_stored_in_responses(app, db, sample_pipeline, tmp_path):
    repo_path = _make_test_repo(tmp_path)
    assessment = create_assessment_from_repo(sample_pipeline.id, repo_path)

    dims = {r.dimension for r in assessment.responses}
    assert "version_control" in dims
    assert "testing" in dims

    # Check that found evidence has detail text
    for r in assessment.responses:
        assert r.notes, f"Response {r.question_key} missing detail text"


def test_detects_gitignore_and_readme(app, db, sample_pipeline, tmp_path):
    repo_path = _make_test_repo(tmp_path)
    assessment = create_assessment_from_repo(sample_pipeline.id, repo_path)

    vc_responses = [r for r in assessment.responses if r.dimension == "version_control"]
    checks = {r.question_key: r.score for r in vc_responses}
    assert checks.get("gitignore") == 1
    assert checks.get("readme") == 1


def test_detects_test_directory(app, db, sample_pipeline, tmp_path):
    repo_path = _make_test_repo(tmp_path)
    assessment = create_assessment_from_repo(sample_pipeline.id, repo_path)

    test_responses = [r for r in assessment.responses if r.dimension == "testing"]
    checks = {r.question_key: r.score for r in test_responses}
    assert checks.get("test_directory") == 1


def test_detects_config_management(app, db, sample_pipeline, tmp_path):
    repo_path = _make_test_repo(tmp_path)
    assessment = create_assessment_from_repo(sample_pipeline.id, repo_path)

    cm_responses = [r for r in assessment.responses if r.dimension == "configuration_management"]
    checks = {r.question_key: r.score for r in cm_responses}
    assert checks.get("env_template") == 1
    assert checks.get("config_directory") == 1


def test_clone_failure_raises(app, db, sample_pipeline):
    import pytest
    with pytest.raises(subprocess.CalledProcessError):
        create_assessment_from_repo(sample_pipeline.id, "https://invalid.example.com/no-such-repo.git")


def test_get_assessment_history(app, db, sample_pipeline, sample_assessment):
    history = get_assessment_history(sample_pipeline.id)
    assert len(history) == 1
    assert history[0].id == sample_assessment.id


def test_get_latest_assessment(app, db, sample_pipeline, sample_assessment):
    latest = get_latest_assessment(sample_pipeline.id)
    assert latest.id == sample_assessment.id


def test_get_latest_assessment_none(app, db, sample_pipeline):
    latest = get_latest_assessment(sample_pipeline.id)
    assert latest is None
