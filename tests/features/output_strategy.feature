Feature: Output Strategy Pattern
  As an AI agent
  I want efficient, machine-readable output by default
  So that I can minimize token usage and processing time

  Background:
    Given I have data to output

  Scenario: Compact output for AI efficiency
    When I format with compact strategy
    Then the output should be compact JSON
    And it should not contain unnecessary whitespace
    And it should be valid JSON

  Scenario: Human-readable output when requested
    When I format with human strategy
    Then the output should be human-readable
    And it should contain descriptive text

  Scenario: AI-optimized result structure
    When I create AI-optimized result
    Then the AI result should use short keys
    And empty values should be omitted
    And essential information should be prioritized

  Scenario: Token efficiency optimization
    When I create AI-optimized result
    Then the result should minimize token usage
    And only essential fields should be included
    And short keys should be used for common fields