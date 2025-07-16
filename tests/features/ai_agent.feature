Feature: AI Agent Interface
  As an AI agent
  I want a high-level interface to development tools
  So that I can efficiently perform complex workflows

  Background:
    Given I have an AI agent initialized with a repository

  Scenario: Fix and propagate workflow
    Given I fixed an error in "shell.nix" at line 249
    When I run the fix and propagate workflow
    Then I should get similar patterns found
    And each pattern should have a safety assessment
    And I should get recommendations for next steps
    And the workflow summary should be informative

  Scenario: Safety assessment for multiple files
    Given I have a list of files to modify
    When I assess the change safety
    Then I should get an overall risk assessment
    And individual file assessments should be provided
    And I should get safety recommendations
    And the safe_to_proceed flag should be accurate

  Scenario: Repository context for decision making
    Given I need to understand the repository state
    When I get the repository context
    Then I should get repository health information
    And blocking issues should be identified
    And I should get recommendations for proceeding
    And the ready_for_changes flag should be accurate

  Scenario: Workflow with no similar patterns
    Given I fixed an isolated error
    When I run the fix and propagate workflow
    Then the pattern count should be 0
    And the summary should indicate the fix is isolated
    And recommendations should reflect no propagation needed

  Scenario: High-risk pattern propagation
    Given I fixed an error in a high-risk file
    When I run the fix and propagate workflow with safety checks
    Then high-risk files should be flagged in recommendations
    And appropriate warnings should be provided
    And the safety analysis should include risk levels