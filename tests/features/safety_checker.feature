Feature: Safety Checker
  As an AI agent
  I want to assess the risk of modifying files
  So that I can avoid breaking critical system configurations

  Background:
    Given I have a repository with various configuration files

  Scenario: Safe file modification
    Given I have a regular development file "src/utils.py"
    When I check the file safety
    Then the risk level should be "SAFE"
    And the exit code should be 0
    And the file should be marked as safe to modify

  Scenario: Medium risk file
    Given I have a configuration file "config/settings.json"
    When I check the file safety
    Then the risk level should be "MEDIUM"
    And the exit code should be 1
    And appropriate warnings should be provided

  Scenario: High risk system file
    Given I have a system configuration "configuration.nix"
    When I check the file safety
    Then the risk level should be "HIGH"
    And the exit code should be 2
    And the file should be marked as high risk

  Scenario: Critical system file
    Given I have a critical file "flake.nix"
    When I check the file safety
    Then the risk level should be "CRITICAL"
    And the exit code should be 3
    And strong warnings should be provided

  Scenario: AI-optimized compact output format
    Given I have any file to check
    When I check the file safety with default format
    Then the output should be compact JSON
    And it should contain essential risk information
    And it should minimize token usage
    
  Scenario: Human-readable output format
    Given I have any file to check
    When I check the file safety with human format
    Then the output should be human-readable text
    And it should contain risk level and warnings

  Scenario: File not found
    Given I provide a non-existent file path
    When I check the file safety
    Then an appropriate error should be returned
    And the exit code should indicate failure