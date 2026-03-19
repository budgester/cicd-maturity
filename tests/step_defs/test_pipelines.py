from pytest_bdd import parsers, scenarios, when

scenarios("pipelines.feature")


@when("I visit the pipelines list")
def visit_pipelines_list(client, response_ctx):
    response_ctx["response"] = client.get("/pipelines/")


@when("I visit the new pipeline form")
def visit_new_pipeline_form(client, response_ctx):
    response_ctx["response"] = client.get("/pipelines/new")


@when(parsers.parse('I submit a new pipeline with url "{url}"'))
def submit_new_pipeline(client, response_ctx, url):
    response_ctx["response"] = client.post(
        "/pipelines/new",
        data={"repository_url": url},
        follow_redirects=False,
    )


@when("I view the pipeline detail page")
def view_pipeline_detail(client, response_ctx, pipeline_ctx):
    pipeline = pipeline_ctx["pipeline"]
    response_ctx["response"] = client.get(f"/pipelines/{pipeline.id}")


@when(parsers.parse("I visit the pipeline with id {pipeline_id:d}"))
def visit_pipeline_by_id(client, response_ctx, pipeline_id):
    response_ctx["response"] = client.get(f"/pipelines/{pipeline_id}")
