Feature: Project Validation
  As an AI development assistant
  I want to validate project structure and code quality
  So that I can ensure projects meet standards before making changes

  Background:
    Given I have a project validator
    And I have a temporary project directory

  Scenario: Validate clean Python project
    Given I create a Python project with:
      | file           | content                                    |
      | pyproject.toml | [project]\nname = "test"\nversion = "1.0.0" |
      | README.md      | # Test Project                             |
      | .gitignore     | __pycache__/                               |
      | src/main.py    | print("Hello World")                       |
      | tests/test_main.py | def test_main(): pass                  |
    When I validate the project
    Then the project should be valid
    And the exit code should be 0
    And there should be no critical or error issues

  Scenario: Detect Python syntax errors
    Given I create a Python project with:
      | file        | content                                    |
      | bad_syntax.py | def broken_function(\n    print('missing paren') |
    When I validate the project with syntax checking
    Then the project should be invalid
    And there should be at least 1 syntax error
    And the exit code should be 2

  Scenario: Detect JSON syntax errors
    Given I create a project with:
      | file     | content                |
      | bad.json | {"key": "value",}      |
    When I validate the project with syntax checking
    Then the project should be invalid
    And there should be at least 1 syntax error
    And the exit code should be 2

  Scenario: Detect missing project structure
    Given I create a minimal project with:
      | file    | content              |
      | main.py | print("Hello")       |
    When I validate the project with structure checking
    Then there should be warnings about missing files
    And the warnings should mention "README.md"
    And the warnings should mention ".gitignore"
    And the exit code should be 1

  Scenario: Detect hardcoded secrets
    Given I create a Python project with:
      | file      | content                                    |
      | config.py | API_KEY = "sk-1234567890abcdef"\npassword = "secret123" |
    When I validate the project with security checking
    Then the project should be invalid
    And there should be critical security issues
    And the exit code should be 3

  Scenario: Validate JavaScript project structure
    Given I create a JavaScript project with:
      | file         | content                                           |
      | package.json | {"name": "test", "version": "1.0.0", "main": "app.js"} |
    When I validate the project with structure checking
    Then there should be an error about missing main file
    And the error should mention "app.js"
    And the exit code should be 2

  Scenario: Skip validation categories
    Given I create a project with issues:
      | file        | content                                    |
      | bad_syntax.py | def broken(                              |
      | config.py   | password = "secret123"                   |
    When I validate the project skipping syntax checking
    Then there should be no syntax errors
    But there should be security issues
    When I validate the project skipping security checking
    Then there should be no security issues
    But there should be syntax errors

  Scenario: Validator exit codes
    Given I create projects with different issue levels
    When I validate a project with no issues
    Then the exit code should be 0
    When I validate a project with warnings only
    Then the exit code should be 1
    When I validate a project with errors
    Then the exit code should be 2
    When I validate a project with critical issues
    Then the exit code should be 3

  Scenario: Validator output formats
    Given I create a project with validation issues
    When I run the validator in silent mode
    Then there should be no output
    When I run the validator in JSON mode
    Then the output should be valid JSON
    And the JSON should contain issue details
    When I run the validator in human mode
    Then the output should be human-readable
    And the output should contain issue summaries

  Scenario: Python dependency validation
    Given I create a Python project with:
      | file           | content                    |
      | pyproject.toml | [project]\ndependencies = ["requests"] |
    When I validate the project with dependency checking
    Then there should be warnings about missing project metadata
    And the warnings should mention missing "name"
    And the warnings should mention missing "version"

  Scenario: Requirements.txt validation
    Given I create a Python project with:
      | file             | content                    |
      | requirements.txt | invalid-requirement-format |
    When I validate the project with dependency checking
    Then there should be warnings about requirement format
    And the exit code should be 1

  Scenario: File skipping during validation
    Given I create a project with files in skip directories:
      | file                    | content              |
      | .git/config             | [core]               |
      | __pycache__/module.pyc  | binary content       |
      | node_modules/lib.js     | module.exports = {}  |
      | src/main.py             | print("Hello")       |
    When I validate the project
    Then only the src/main.py file should be checked
    And files in skip directories should be ignored