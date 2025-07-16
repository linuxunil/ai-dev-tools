Feature: Project Context Analysis
  As an AI development assistant
  I want to analyze project context automatically
  So that I can make informed decisions about code modifications

  Background:
    Given I have a context analyzer
    And I have a temporary project directory

  Scenario: Analyze Python project with dependencies
    Given I create a Python project with:
      | file           | content                                    |
      | pyproject.toml | [project]\nname = "test"\ndependencies = ["requests>=2.0.0", "click"] |
      | main.py        | print("Hello World")                      |
      | src/app.py     | from fastapi import FastAPI               |
    When I analyze the project context
    Then the project type should be "python"
    And the framework should be "fastapi"
    And there should be at least 2 dependencies
    And the complexity score should be greater than 0

  Scenario: Analyze JavaScript project with React
    Given I create a JavaScript project with:
      | file        | content                                                    |
      | package.json| {"name": "test", "dependencies": {"react": "^18.0.0"}}   |
      | index.js    | import React from 'react';                                |
    When I analyze the project context
    Then the project type should be "javascript"
    And the framework should be "react"
    And there should be at least 1 dependency

  Scenario: Analyze mixed-language project
    Given I create a mixed project with:
      | file         | content                    |
      | package.json | {"name": "test"}          |
      | pyproject.toml| [project]\nname = "test" |
      | main.py      | print("Python")          |
      | index.js     | console.log("JS");        |
    When I analyze the project context
    Then the project type should be "mixed"

  Scenario: Context analyzer exit codes
    Given I create a simple project with:
      | file    | content              |
      | main.py | print("Hello")       |
    When I run the context analyzer CLI in silent mode
    Then the exit code should be the complexity score
    And the exit code should be between 0 and 254

  Scenario: Context analyzer output formats
    Given I create a Python project with:
      | file    | content              |
      | main.py | print("Hello")       |
    When I run the context analyzer with format "json"
    Then the output should be valid JSON
    And the JSON should contain "project_type"
    And the JSON should contain "complexity_score"