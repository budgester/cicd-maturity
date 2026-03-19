import os
import subprocess

import pytest

from app.services.git_analyzer import GitAnalyzer


@pytest.fixture
def test_repo(tmp_path):
    """Create a test git repo with various files to detect."""
    repo = tmp_path / "test-repo"
    repo.mkdir()

    # Basic files
    (repo / "README.md").write_text("# Test Project\n")
    (repo / ".gitignore").write_text("*.pyc\n__pycache__/\n.env\n*.key\n")
    (repo / ".editorconfig").write_text("[*]\nindent_style = space\n")

    # Python project
    (repo / "requirements.txt").write_text("flask>=3.0\npytest>=8.0\nstructlog>=23.0\nprometheus-client>=0.19\n")
    (repo / "pyproject.toml").write_text(
        '[project]\nname = "test"\n\n[tool.pytest.ini_options]\ntestpaths = ["tests"]\n\n'
        '[tool.coverage.run]\nsource = ["app"]\n'
    )

    # Config
    config_dir = repo / "config"
    config_dir.mkdir()
    (config_dir / "settings.py").write_text("DEBUG = True\n")
    (repo / ".env.example").write_text("SECRET_KEY=changeme\n")

    # Tests
    tests_dir = repo / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_app.py").write_text("def test_app():\n    assert True\n")

    # CI
    workflows_dir = repo / ".github" / "workflows"
    workflows_dir.mkdir(parents=True)
    (workflows_dir / "ci.yml").write_text(
        "name: CI\non: push\njobs:\n  test:\n    runs-on: ubuntu-latest\n    steps:\n"
        "      - uses: actions/checkout@v4\n      - run: pip install -r requirements.txt\n"
        "      - run: pytest --cov\n      - run: ruff check .\n"
    )

    # Dockerfile
    (repo / "Dockerfile").write_text("FROM python:3.12\nCOPY . /app\n")

    # AI readiness files
    (repo / "CLAUDE.md").write_text(
        "# Project\n\nThis is a Python Flask project using SQLAlchemy ORM.\n\n"
        "## Tech Stack\n\n- Python 3.12 with Flask\n- SQLAlchemy via Flask-SQLAlchemy\n"
        "- Flask-Migrate for database migrations\n- pytest for testing\n\n"
        "## Conventions\n\n- Use snake_case for everything (files, functions, variables)\n"
        "- Routes go in app/routes/ as Flask Blueprints\n"
        "- Business logic goes in app/services/, not in routes\n"
        "- Models go in app/models/\n- Tests mirror the app/ structure under tests/\n\n"
        "## Commands\n\n- pytest to run tests\n- python run.py to start dev server\n"
        "- flask db upgrade to apply migrations\n- flask db migrate to generate migrations\n\n"
        "## Architecture\n\nUse the app factory pattern. Config via environment variables.\n"
        "Keep routes thin, put logic in services. Use dependency injection.\n"
    )

    # Dependabot
    (repo / ".github" / "dependabot.yml").write_text(
        "version: 2\nupdates:\n  - package-ecosystem: pip\n    directory: /\n    schedule:\n      interval: weekly\n"
    )

    # Pre-commit
    (repo / ".pre-commit-config.yaml").write_text(
        "repos:\n  - repo: https://github.com/Yelp/detect-secrets\n    hooks:\n      - id: detect-secrets\n"
    )

    env = {
        "GIT_AUTHOR_NAME": "Test",
        "GIT_AUTHOR_EMAIL": "t@t.com",
        "GIT_COMMITTER_NAME": "Test",
        "GIT_COMMITTER_EMAIL": "t@t.com",
        "HOME": str(tmp_path),
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
    }
    subprocess.run(["git", "init", str(repo)], capture_output=True, check=True, env=env)
    subprocess.run(["git", "add", "."], cwd=repo, capture_output=True, check=True, env=env)
    subprocess.run(
        ["git", "commit", "-m", "feat: initial setup with CI and tests\n\nCo-Authored-By: Claude <noreply@anthropic.com>"],
        cwd=repo, capture_output=True, check=True, env=env,
    )
    subprocess.run(
        ["git", "tag", "v1.0.0"],
        cwd=repo, capture_output=True, check=True, env=env,
    )
    return str(repo)


def test_analyzer_returns_all_dimensions(test_repo):
    analyzer = GitAnalyzer(test_repo)
    results = analyzer.analyze()
    dims = results["dimensions"]

    expected_dims = [
        "version_control", "build_process", "testing", "deployment",
        "monitoring", "security", "configuration_management", "feedback_loops",
        "ai_readiness",
    ]
    for dim in expected_dims:
        assert dim in dims, f"Missing dimension: {dim}"
        assert "score" in dims[dim]
        assert "evidence" in dims[dim]
        assert 1 <= dims[dim]["score"] <= 5

    # Classification
    assert "classification" in results
    assert "primary_type" in results["classification"]
    assert "signals" in results["classification"]


def test_detects_version_control_evidence(test_repo):
    analyzer = GitAnalyzer(test_repo)
    results = analyzer.analyze()
    vc = results["dimensions"]["version_control"]

    checks = {e["check"]: e for e in vc["evidence"]}
    assert checks["gitignore"]["found"]
    assert checks["readme"]["found"]
    assert vc["score"] >= 2


def test_detects_build_process_evidence(test_repo):
    analyzer = GitAnalyzer(test_repo)
    results = analyzer.analyze()
    bp = results["dimensions"]["build_process"]

    checks = {e["check"]: e for e in bp["evidence"]}
    assert any(e["found"] for e in bp["evidence"] if e["check"] == "ci_config")
    assert checks["containerised_build"]["found"]
    assert bp["score"] >= 3


def test_detects_testing_evidence(test_repo):
    analyzer = GitAnalyzer(test_repo)
    results = analyzer.analyze()
    t = results["dimensions"]["testing"]

    checks = {e["check"]: e for e in t["evidence"]}
    assert checks["test_directory"]["found"]
    assert t["score"] >= 2


def test_detects_deployment_evidence(test_repo):
    analyzer = GitAnalyzer(test_repo)
    results = analyzer.analyze()
    d = results["dimensions"]["deployment"]

    checks = {e["check"]: e for e in d["evidence"]}
    assert checks["dockerfile"]["found"]
    assert d["score"] >= 2


def test_detects_monitoring_evidence(test_repo):
    analyzer = GitAnalyzer(test_repo)
    results = analyzer.analyze()
    m = results["dimensions"]["monitoring"]

    # structlog and prometheus-client in deps
    checks = {e["check"]: e for e in m["evidence"]}
    assert checks.get("logging_library", {}).get("found") or checks.get("structured_logging", {}).get("found")
    assert m["score"] >= 2


def test_detects_security_evidence(test_repo):
    analyzer = GitAnalyzer(test_repo)
    results = analyzer.analyze()
    s = results["dimensions"]["security"]

    checks = {e["check"]: e for e in s["evidence"]}
    assert checks["dependency_scanning"]["found"]
    assert checks["pre_commit"]["found"]
    assert checks["secret_detection"]["found"]
    assert s["score"] >= 3


def test_detects_config_management_evidence(test_repo):
    analyzer = GitAnalyzer(test_repo)
    results = analyzer.analyze()
    cm = results["dimensions"]["configuration_management"]

    checks = {e["check"]: e for e in cm["evidence"]}
    assert checks["env_template"]["found"]
    assert checks["config_directory"]["found"]
    assert cm["score"] >= 2


def test_detects_feedback_loops_evidence(test_repo):
    analyzer = GitAnalyzer(test_repo)
    results = analyzer.analyze()
    fl = results["dimensions"]["feedback_loops"]

    assert fl["score"] >= 1
    assert len(fl["evidence"]) > 0


def test_detects_ai_readiness_evidence(test_repo):
    analyzer = GitAnalyzer(test_repo)
    results = analyzer.analyze()
    ai = results["dimensions"]["ai_readiness"]

    checks = {e["check"]: e for e in ai["evidence"]}
    assert checks["claude_md"]["found"]
    assert checks["claude_md_detailed"]["found"]  # >500 chars
    assert checks["ai_coauthored"]["found"]
    assert ai["score"] >= 3


def test_classifies_web_application(test_repo):
    analyzer = GitAnalyzer(test_repo)
    results = analyzer.analyze()
    classification = results["classification"]

    assert classification["primary_type"] == "web_app"
    assert classification["primary_label"] == "Web Application"
    assert classification["confidence"] > 0
    assert len(classification["signals"]) > 0
    assert any("flask" in s.lower() for s in classification["signals"])


def test_invalid_repo_raises():
    analyzer = GitAnalyzer("https://invalid.example.com/no-such-repo.git")
    with pytest.raises(subprocess.CalledProcessError):
        analyzer.analyze()
