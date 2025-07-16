Feature: Pattern Scanner
  As an AI agent
  I want to find similar code patterns
  So that I can apply consistent fixes across a codebase

  Background:
    Given I have a repository with multiple files
    And the files contain similar code patterns

  Scenario: Find similar patterns with exit code communication
    Given I have a file "shell.nix" with mkIf pattern at line 10
    When I scan for similar patterns with default format
    Then I should find other mkIf patterns
    And the exit code should equal the number of patterns found
    And there should be no output by default (silent mode)

  Scenario: No similar patterns found
    Given I have a file "unique.nix" with a unique pattern at line 5
    When I scan for similar patterns with default format
    Then I should find 0 similar patterns
    And the exit code should be 0
    And there should be no output (exit code communication only)

  Scenario: Pattern type detection
    Given I have a file with "home.packages" and "mkIf" at line 15
    When I scan for similar patterns
    Then the pattern type should be detected as "mkIf_home_packages"
    And only similar mkIf home.packages patterns should be found

  Scenario: Exit code encodes pattern count (most efficient)
    Given I have 3 files with similar mkIf patterns
    When I scan for patterns with default format
    Then the exit code should be 3
    And there should be no output (pure exit code communication)
    
  Scenario: Output only when explicitly requested
    Given I have 3 files with similar mkIf patterns
    When I scan for patterns with compact format
    Then the exit code should be 3
    And the output should be compact JSON

  Scenario: CLI argument validation
    Given I provide an invalid target format "file-without-line"
    When I run the pattern scanner
    Then the exit code should be 255
    And an error message should be displayed

  Scenario: File not found error
    Given I provide a target "nonexistent.nix:10"
    When I run the pattern scanner
    Then the exit code should be 255
    And an error message should indicate file not found