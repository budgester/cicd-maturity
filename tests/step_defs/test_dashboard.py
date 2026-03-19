from pytest_bdd import scenarios, when


scenarios("dashboard.feature")


@when("I visit the dashboard")
def visit_dashboard(client, response_ctx):
    response_ctx["response"] = client.get("/")
