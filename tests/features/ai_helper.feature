Feature: AI Helper - Unified AI assistant with tool orchestration
  As an AI agent
  I want to use unified workflows for project analysis and systematic fixes
  So that I can efficiently orchestrate all development tools

  Background:
    Given I have a test project directory
    And the AI Helper is initialized

  Scenario: Analyze project with good health
    Given the repository has good health
    And context analysis shows low complexity
    And validation finds no issues
    When I run project analysis
    Then the analysis should succeed
    And the project should be ready for AI assistance
    And the exit code should reflect the health score

  Scenario: Analyze project with syntax errors
    Given the repository has syntax errors
    When I run project analysis
    Then the analysis should succeed
    And the project should not be ready for AI assistance
    And the recommendations should include fixing syntax errors
    And the exit code should be low

  Scenario: Plan changes for safe files
    Given I have target files to modify
    And the files are safe to modify
    When I run change planning
    Then the planning should succeed
    And the changes should be safe to proceed
    And the exit code should indicate low risk

  Scenario: Plan changes for critical files
    Given I have target files to modify
    And the files are critical system files
    When I run change planning
    Then the planning should succeed
    And the changes should require caution
    And the recommendations should include backup warnings
    And the exit code should indicate high risk

  Scenario: Systematic fix workflow with patterns found
    Given I have fixed an issue at a specific location
    And similar patterns exist in the codebase
    And some patterns are in safe files
    When I run systematic fix workflow
    Then the workflow should succeed
    And similar patterns should be found
    And safe files should be identified
    And the exit code should equal the pattern count

  Scenario: Systematic fix workflow with no patterns
    Given I have fixed an issue at a specific location
    And no similar patterns exist in the codebase
    When I run systematic fix workflow
    Then the workflow should succeed
    And no patterns should be found
    And the fix should be marked as unique
    And the exit code should be zero

  Scenario: Compare configurations with differences
    Given I have two different configuration files
    When I run configuration comparison
    Then the comparison should succeed
    And differences should be found
    And the exit code should equal the difference count

  Scenario: Compare identical configurations
    Given I have two identical configuration files
    When I run configuration comparison
    Then the comparison should succeed
    And no differences should be found
    And the files should be marked as identical
    And the exit code should be zero

  Scenario: Handle workflow errors gracefully
    Given an invalid project path is provided
    When I run any workflow
    Then the workflow should fail gracefully
    And error information should be provided
    And the exit code should be 255

  Scenario: AI Helper CLI integration
    Given the AI Helper CLI is available
    When I run "ai-helper workflows"
    Then all available workflows should be listed
    And usage information should be provided
    And the exit code should be zero

  Scenario: Silent mode for AI consumption
    Given I want to use AI Helper for automated workflows
    When I run workflows without format flag
    Then no output should be produced
    And only exit codes should be returned
    And the exit codes should encode workflow results