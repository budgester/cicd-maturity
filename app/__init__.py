import os
import re
from urllib.parse import urlparse

from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

from config.settings import config_by_name

db = SQLAlchemy()
migrate = Migrate()


def repo_file_url(repo_url, file_path):
    """Convert a repo URL + file path to a browsable URL."""
    if not repo_url or not file_path:
        return None

    # Normalise SSH to HTTPS
    ssh_match = re.match(r"git@([^:]+):(.+?)(?:\.git)?$", repo_url)
    if ssh_match:
        host = ssh_match.group(1)
        path = ssh_match.group(2)
    else:
        parsed = urlparse(repo_url)
        host = parsed.hostname or ""
        path = parsed.path.strip("/")
        path = re.sub(r"\.git$", "", path)

    if not host or not path:
        return None

    if "github" in host:
        return f"https://{host}/{path}/blob/HEAD/{file_path}"
    elif "gitlab" in host:
        return f"https://{host}/{path}/-/blob/HEAD/{file_path}"
    elif "bitbucket" in host:
        return f"https://{host}/{path}/src/HEAD/{file_path}"
    else:
        return f"https://{host}/{path}/blob/HEAD/{file_path}"


def create_app(config_name=None):
    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "development")

    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])

    db.init_app(app)
    migrate.init_app(app, db)

    app.jinja_env.filters["repo_file_url"] = lambda path, repo_url: repo_file_url(repo_url, path)

    from app.routes.assessments import assessments_bp
    from app.routes.main import main_bp
    from app.routes.pipelines import pipelines_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(pipelines_bp, url_prefix="/pipelines")
    app.register_blueprint(assessments_bp)

    return app
