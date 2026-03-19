import os

from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

from config.settings import config_by_name

db = SQLAlchemy()
migrate = Migrate()


def create_app(config_name=None):
    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "development")

    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])

    db.init_app(app)
    migrate.init_app(app, db)

    from app.routes.main import main_bp
    from app.routes.pipelines import pipelines_bp
    from app.routes.assessments import assessments_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(pipelines_bp, url_prefix="/pipelines")
    app.register_blueprint(assessments_bp)

    return app
