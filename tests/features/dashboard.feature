Feature: Dashboard
  The dashboard gives an overview of all pipelines in the system.

  Scenario: View empty dashboard
    Given the database is empty
    When I visit the dashboard
    Then the response status code should be 200
    And the page should contain "Pipeline Maturity"
    And the page should contain "No pipelines yet"

  Scenario: View dashboard with a pipeline
    Given a pipeline exists with name "payments-api"
    When I visit the dashboard
    Then the response status code should be 200
    And the page should contain "payments-api"
