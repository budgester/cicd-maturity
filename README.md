# CI/CD Maturity Assessment

Evidence-based CI/CD pipeline maturity assessment tool. Analyses git repositories to produce maturity scores across 9 dimensions, generates actionable recommendations based on *Continuous Delivery* (Farley & Humble) and the DORA metrics framework.

## Features

- Automated evidence-based assessment from a git URL (no manual questionnaire)
- Pipeline name and team auto-detected from repository URL
- 9 assessment dimensions: version control, build process, testing, deployment, monitoring, security, configuration management, feedback loops (DORA), AI readiness
- Radar chart and trend visualisation (Chart.js)
- Prioritised recommendations with concrete actions and book references
- PDF report export
- Maturity model reference page

## Quick Start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
flask db upgrade
python run.py
```

Open http://127.0.0.1:5000, add a pipeline by entering a git URL, and run an assessment.

## Tests

```bash
pip install -r requirements-dev.txt
pytest
```

## Docker

```bash
docker build -t cicd-maturity .
docker run -p 5000:5000 cicd-maturity
```
