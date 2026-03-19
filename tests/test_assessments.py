from unittest.mock import patch


def test_new_assessment_page(client, sample_pipeline):
    # Need a repo URL set
    from app import db
    sample_pipeline.repository_url = "https://example.com/repo.git"
    db.session.commit()

    resp = client.get(f"/pipelines/{sample_pipeline.id}/assessments/new")
    assert resp.status_code == 200
    assert b"Analyse Repository" in resp.data


def test_new_assessment_redirects_without_repo_url(client, sample_pipeline):
    resp = client.get(f"/pipelines/{sample_pipeline.id}/assessments/new", follow_redirects=False)
    assert resp.status_code == 302


def test_create_assessment_via_post(client, sample_pipeline, sample_assessment):
    """Mock the analyzer so we don't need a real repo."""
    from app import db
    sample_pipeline.repository_url = "https://example.com/repo.git"
    db.session.commit()

    mock_results = {
        dim: {"score": 3, "evidence": [{"check": "test_check", "found": True, "detail": "test detail"}]}
        for dim in [
            "version_control", "build_process", "testing", "deployment",
            "monitoring", "security", "configuration_management", "feedback_loops",
        ]
    }

    with patch("app.services.assessment_service.GitAnalyzer") as MockAnalyzer:
        MockAnalyzer.return_value.analyze.return_value = mock_results
        resp = client.post(
            f"/pipelines/{sample_pipeline.id}/assessments/",
            data={"assessed_by": "tester"},
            follow_redirects=False,
        )
    assert resp.status_code == 302
    assert "/assessments/" in resp.headers["Location"]


def test_create_assessment_handles_clone_failure(client, sample_pipeline):
    import subprocess
    from app import db
    sample_pipeline.repository_url = "https://example.com/repo.git"
    db.session.commit()

    with patch("app.services.assessment_service.GitAnalyzer") as MockAnalyzer:
        MockAnalyzer.return_value.analyze.side_effect = subprocess.CalledProcessError(128, "git clone")
        resp = client.post(
            f"/pipelines/{sample_pipeline.id}/assessments/",
            data={},
            follow_redirects=True,
        )
    assert resp.status_code == 200
    assert b"Failed to clone" in resp.data


def test_view_assessment(client, sample_pipeline, sample_assessment):
    resp = client.get(f"/pipelines/{sample_pipeline.id}/assessments/{sample_assessment.id}")
    assert resp.status_code == 200
    assert b"Assessment Results" in resp.data
    assert b"Level 3" in resp.data


def test_assessment_history(client, sample_pipeline, sample_assessment):
    resp = client.get(f"/pipelines/{sample_pipeline.id}/assessments/")
    assert resp.status_code == 200
    assert b"Assessment History" in resp.data


def test_assessment_history_empty(client, sample_pipeline):
    resp = client.get(f"/pipelines/{sample_pipeline.id}/assessments/")
    assert resp.status_code == 200
    assert b"No assessments yet" in resp.data


def test_pipeline_view_shows_assessment_button(client, sample_pipeline):
    from app import db
    sample_pipeline.repository_url = "https://example.com/repo.git"
    db.session.commit()

    resp = client.get(f"/pipelines/{sample_pipeline.id}")
    assert resp.status_code == 200
    assert b"New Assessment" in resp.data


def test_pipeline_view_shows_latest_badge(client, sample_pipeline, sample_assessment):
    resp = client.get(f"/pipelines/{sample_pipeline.id}")
    assert resp.status_code == 200
    assert b"Level 3" in resp.data


def test_index_shows_maturity_badge(client, sample_pipeline, sample_assessment):
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"L3:" in resp.data


def test_export_pdf(client, sample_pipeline, sample_assessment):
    resp = client.get(f"/pipelines/{sample_pipeline.id}/assessments/{sample_assessment.id}/pdf")
    assert resp.status_code == 200
    assert resp.headers["Content-Type"] == "application/pdf"
    assert b"%PDF" in resp.data
