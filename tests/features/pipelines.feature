Feature: Pipeline management
  Users can list, create, and view pipelines.

  Scenario: List pipelines when none exist
    Given the database is empty
    When I visit the pipelines list
    Then the response status code should be 200
    And the page should contain "No pipelines found"

  Scenario: List pipelines with data
    Given a pipeline exists with name "checkout-service"
    When I visit the pipelines list
    Then the response status code should be 200
    And the page should contain "checkout-service"

  Scenario: View the new pipeline form
    Given the database is empty
    When I visit the new pipeline form
    Then the response status code should be 200
    And the page should contain "Add Pipeline"

  Scenario: Create a new pipeline
    Given the database is empty
    When I submit a new pipeline with url "https://github.com/backend/order-service.git"
    Then the response should redirect
    And I follow the redirect
    And the page should contain "order-service"

  Scenario: View a pipeline detail page
    Given a pipeline exists with name "search-service"
    When I view the pipeline detail page
    Then the response status code should be 200
    And the page should contain "search-service"

  Scenario: View a non-existent pipeline returns 404
    Given the database is empty
    When I visit the pipeline with id 9999
    Then the response status code should be 404
