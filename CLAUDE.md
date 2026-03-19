# Pipeline Maturity

A Python/Flask application for assessing and visualising software development pipeline maturity. It tracks the health, status, and tooling across a full software development lifecycle.

## Project Structure

```
pipeline-maturity/
├── app/                    # Flask application package
│   ├── __init__.py         # App factory
│   ├── models/             # SQLAlchemy models
│   ├── routes/             # Blueprint route handlers
│   ├── services/           # Business logic
│   ├── templates/          # Jinja2 templates
│   └── static/             # CSS, JS, images
├── tests/                  # Test suite
│   ├── conftest.py         # Shared fixtures (app, client, db)
│   ├── features/           # Gherkin feature files
│   └── step_defs/          # BDD step definitions
├── config/                 # Configuration files
├── migrations/             # Alembic DB migrations (auto-generated)
├── requirements.txt        # Python dependencies
├── pyproject.toml          # Project metadata and tool config
└── run.py                  # Development entry point
```

## Tech Stack

- **Python 3.11+** with **Flask**
- **SQLAlchemy** via Flask-SQLAlchemy for ORM
- **Flask-Migrate** (Alembic) for database migrations
- **SQLite** for development, PostgreSQL for production
- **Jinja2** templates with Bootstrap for UI
- **pytest** with **pytest-bdd** for BDD testing

## Commands

- `python run.py` — run the dev server
- `pytest` — run tests
- `flask db upgrade` — apply database migrations
- `flask db migrate -m "description"` — generate a new migration
- `pip install -r requirements.txt` — install dependencies

## Conventions

- Use the app factory pattern (`create_app()` in `app/__init__.py`)
- Routes go in `app/routes/` as Flask Blueprints
- Business logic goes in `app/services/`, not in routes
- Models go in `app/models/`
- Config via environment variables, loaded in `config/settings.py`
- Tests mirror the `app/` structure under `tests/`
- Use snake_case for everything (files, functions, variables)

## BDD Workflow

Features are spec-driven using Gherkin (`.feature` files) with pytest-bdd.

### Adding a new feature

1. Write a `.feature` file in `tests/features/`
2. Create a matching `tests/step_defs/test_<feature>.py` with `scenarios("<feature>.feature")`
3. Add feature-specific `@when` steps in that file
4. Add reusable `@given`/`@then` steps in `tests/step_defs/conftest.py`
5. Run `pytest -v` to verify

### Step placement

- **Shared steps** (`@given`, `@then` for common assertions) go in `tests/step_defs/conftest.py`
- **Feature-specific steps** (`@when` actions) go in `tests/step_defs/test_<feature>.py`
