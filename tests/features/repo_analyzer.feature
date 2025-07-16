Feature: Repository Analyzer
  As an AI agent
  I want to quickly assess repository health
  So that I can determine if it's safe to make changes

  Background:
    Given I have a repository to analyze

  Scenario: Healthy repository
    Given the repository has no uncommitted changes
    And there are no syntax errors
    When I analyze the repository health
    Then the repository should be marked as clean
    And the exit code should be 0
    And it should be ready for changes

  Scenario: Repository with uncommitted changes
    Given the repository has uncommitted changes
    When I analyze the repository health
    Then the repository should be marked as not clean
    And it should not be ready for changes
    And the status should indicate uncommitted changes

  Scenario: Repository with syntax errors
    Given the repository has 2 syntax errors
    When I analyze the repository health
    Then the exit code should be 2
    And the syntax error count should be reported
    And it should not be ready for changes

  Scenario: JSON output format
    Given I have any repository
    When I analyze the repository with JSON format
    Then the output should be valid JSON
    And it should contain is_clean, syntax_errors, and ready_for_changes

  Scenario: Exit code encodes error count
    Given the repository has 5 syntax errors
    When I analyze the repository health
    Then the exit code should be 5
    And the JSON should show syntax_errors as 5