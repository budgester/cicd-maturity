import pytest
from pytest_bdd import given, then, parsers

from app.models.pipeline import Pipeline


@pytest.fixture
def response_ctx():
    """Mutable dict to pass HTTP responses between steps."""
    return {}


@pytest.fixture
def pipeline_ctx():
    """Mutable dict to pass model instances between steps."""
    return {}


@given("the database is empty")
def database_is_empty():
    """No-op -- the test database is recreated empty for each test."""
    pass


@given(parsers.parse('a pipeline exists with name "{name}"'))
def create_pipeline(db, name, pipeline_ctx):
    pipeline = Pipeline(name=name)
    db.session.add(pipeline)
    db.session.commit()
    pipeline_ctx["pipeline"] = pipeline


@then(parsers.parse("the response status code should be {code:d}"))
def check_status_code(response_ctx, code):
    assert response_ctx["response"].status_code == code


@then(parsers.parse('the page should contain "{text}"'))
def page_contains(response_ctx, text):
    assert text.encode() in response_ctx["response"].data


@then("the response should redirect")
def response_redirects(response_ctx):
    assert response_ctx["response"].status_code in (301, 302, 303)


@then("I follow the redirect")
def follow_redirect(client, response_ctx):
    response_ctx["response"] = client.get(
        response_ctx["response"].headers["Location"],
        follow_redirects=False,
    )
