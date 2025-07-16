Feature: Impact Analysis
  As an AI development tool
  I want to analyze the impact of changes to files
  So that I can understand what other parts of the project might be affected

  Background:
    Given I have an impact analyzer

  Scenario: Analyze isolated file with no dependencies
    Given I have an isolated file with no dependencies
    When I analyze the impact of the file
    Then the analysis should show no impact
    And the exit code should be 0

  Scenario: Analyze file with dependency impact
    Given I have a module file and a file that imports it
    When I analyze the impact of the module file
    Then the analysis should show dependency impact
    And the impacted files should include the importing file
    And the exit code should reflect the impact severity

  Scenario: Analyze file with API impact
    Given I have an API file with function definitions and a consumer file
    When I analyze the impact of the API file
    Then the analysis should show API impact
    And the impact severity should be medium or high
    And the exit code should reflect the impact severity

  Scenario: Analyze configuration file impact
    Given I have a configuration file and related build files
    When I analyze the impact of the configuration file
    Then the analysis should show configuration impact
    And the impacted files should include build-related files
    And the exit code should reflect the impact severity

  Scenario: Analyze build file impact
    Given I have a build file and multiple code files
    When I analyze the impact of the build file
    Then the analysis should show critical build impact
    And the impact severity should be critical
    And the exit code should reflect the high impact

  Scenario: Analyze test file impact
    Given I have a code file and its corresponding test file
    When I analyze the impact of the code file
    Then the analysis should show test impact
    And the impacted files should include the test file
    And the exit code should reflect the impact severity

  Scenario: Analyze non-existent file
    Given I have a path to a non-existent file
    When I attempt to analyze the impact
    Then the operation should fail with file not found error
    And the exit code should be 255

  Scenario: Analyze file outside project
    Given I have a file outside the project directory
    When I analyze the impact of the external file
    Then the analysis should show minimal or no impact
    And the exit code should be low

  Scenario: Silent mode operation
    Given I have a file with some dependencies
    When I run the impact analysis in silent mode
    Then there should be no output
    And the exit code should indicate the impact severity

  Scenario: JSON output format
    Given I have a file with some dependencies
    When I run the impact analysis with JSON output
    Then the output should be valid JSON
    And the JSON should contain impact details
    And the exit code should indicate the impact severity

  Scenario: Human-readable output format
    Given I have a file with some dependencies
    When I run the impact analysis with human-readable output
    Then the output should contain a summary
    And the output should list impacted files
    And the output should include recommendations
    And the exit code should indicate the impact severity

  Scenario: High impact scenario with many dependencies
    Given I have a central file with many dependencies
    When I analyze the impact of the central file
    Then the analysis should show high impact
    And the severity score should be significant
    And the exit code should reflect the high impact

  Scenario: Impact severity calculation
    Given I have files with different types of impact
    When I analyze the impact of each file
    Then the severity scores should vary appropriately
    And higher impact files should have higher scores
    And the exit codes should reflect the relative impact levels

  Scenario: Recommendations generation
    Given I have a file that affects APIs and build system
    When I analyze the impact of the file
    Then the analysis should include relevant recommendations
    And the recommendations should mention testing and compatibility
    And the exit code should reflect the impact severity

  Scenario: Maximum files limit
    Given I have a file that impacts many other files
    When I run the impact analysis with a file limit
    Then the output should be limited to the specified number of files
    And the summary should indicate truncation
    And the exit code should still reflect the full impact