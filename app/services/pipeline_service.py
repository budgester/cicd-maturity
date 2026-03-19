import re
from urllib.parse import urlparse

from app import db
from app.models.pipeline import Pipeline, PipelineStage


def extract_team_from_url(repo_url):
    """Extract the org/user from a git repository URL."""
    if not repo_url:
        return ""

    # SSH format: git@host:org/repo.git
    ssh_match = re.match(r"git@[^:]+:([^/]+)", repo_url)
    if ssh_match:
        return ssh_match.group(1)

    # HTTPS format
    parsed = urlparse(repo_url)
    path = parsed.path.strip("/")
    if path:
        parts = path.split("/")
        if len(parts) >= 1:
            return parts[0]

    return ""


def extract_name_from_url(repo_url):
    """Extract the repo name from a git repository URL."""
    if not repo_url:
        return ""

    # SSH format: git@host:org/repo.git
    ssh_match = re.match(r"git@[^:]+:[^/]+/(.+?)(?:\.git)?$", repo_url)
    if ssh_match:
        return ssh_match.group(1)

    # HTTPS format
    parsed = urlparse(repo_url)
    path = parsed.path.strip("/")
    if path:
        parts = path.split("/")
        if len(parts) >= 2:
            return re.sub(r"\.git$", "", parts[-1])

    return ""


def get_all_pipelines():
    return db.session.scalars(db.select(Pipeline).order_by(Pipeline.name)).all()


def get_pipeline(pipeline_id):
    return db.get_or_404(Pipeline, pipeline_id)


def create_pipeline_from_url(repository_url):
    name = extract_name_from_url(repository_url) or repository_url
    team = extract_team_from_url(repository_url)

    pipeline = Pipeline(
        name=name,
        repository_url=repository_url,
        team=team,
    )
    db.session.add(pipeline)
    db.session.commit()
    return pipeline


def delete_pipeline(pipeline_id):
    pipeline = db.get_or_404(Pipeline, pipeline_id)
    db.session.delete(pipeline)
    db.session.commit()


def add_stage(pipeline_id, name, tool="", status="unknown", config_url="", notes=""):
    stage = PipelineStage(
        pipeline_id=pipeline_id,
        name=name,
        tool=tool,
        status=status,
        config_url=config_url,
        notes=notes,
    )
    db.session.add(stage)
    db.session.commit()
    return stage


def update_stage(stage_id, **kwargs):
    stage = db.get_or_404(PipelineStage, stage_id)
    for key, value in kwargs.items():
        if hasattr(stage, key):
            setattr(stage, key, value)
    db.session.commit()
    return stage


def delete_stage(stage_id):
    stage = db.get_or_404(PipelineStage, stage_id)
    db.session.delete(stage)
    db.session.commit()
