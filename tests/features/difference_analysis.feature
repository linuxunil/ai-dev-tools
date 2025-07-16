Feature: Difference Analysis
  As an AI development tool
  I want to analyze differences between files and directories
  So that I can understand changes and their significance

  Background:
    Given I have a difference analyzer

  Scenario: Compare identical files
    Given I have two identical text files
    When I compare the files
    Then the analysis should show no differences
    And the exit code should be 0

  Scenario: Compare files with minor differences
    Given I have two text files with minor content differences
    When I compare the files
    Then the analysis should show 1 difference
    And the difference should be marked as minor or major significance
    And the exit code should be 1

  Scenario: Compare files with critical differences
    Given I have two Python files with function definition changes
    When I compare the files
    Then the analysis should show 1 difference
    And the difference should be marked as critical significance
    And the exit code should be 1

  Scenario: Compare files with whitespace differences
    Given I have two files that differ only in whitespace
    When I compare the files with whitespace ignored
    Then the analysis should show no differences
    And the exit code should be 0

  Scenario: Compare files with whitespace differences strictly
    Given I have two files that differ only in whitespace
    When I compare the files with whitespace not ignored
    Then the analysis should show 1 difference
    And the exit code should be 1

  Scenario: Compare directories with mixed changes
    Given I have two directories with added, removed, and modified files
    When I compare the directories
    Then the analysis should show multiple differences
    And the analysis should correctly count added, removed, and modified files
    And the exit code should reflect the number of significant differences

  Scenario: Compare non-existent files
    Given I have paths to non-existent files
    When I attempt to compare the files
    Then the operation should fail with file not found error
    And the exit code should be 255

  Scenario: Compare binary files
    Given I have two different binary files
    When I compare the files
    Then the analysis should detect binary file changes
    And the exit code should be 1

  Scenario: Silent mode operation
    Given I have two different text files
    When I run the comparison in silent mode
    Then there should be no output
    And the exit code should indicate the number of differences

  Scenario: JSON output format
    Given I have two different text files
    When I run the comparison with JSON output
    Then the output should be valid JSON
    And the JSON should contain difference details
    And the exit code should indicate the number of differences

  Scenario: Human-readable output format
    Given I have two different text files
    When I run the comparison with human-readable output
    Then the output should contain a summary
    And the output should list individual differences
    And the exit code should indicate the number of differences

  Scenario: Maximum differences handling
    Given I have two directories with many differences
    When I compare the directories
    Then the exit code should be capped at 254
    And the analysis should handle large numbers of differences gracefully