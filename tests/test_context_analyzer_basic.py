"""
Basic tests for ContextAnalyzer functionality
"""

import json
import tempfile
from pathlib import Path

import pytest

from ai_dev_tools.core.context_analyzer import (
    ContextAnalyzer,
    FrameworkType,
    ProjectType,
)


class TestContextAnalyzer:
    """Test ContextAnalyzer core functionality"""

    def test_python_project_detection(self):
        """Test detection of Python projects"""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)

            # Create Python project files
            (project_path / "pyproject.toml").write_text("""
[project]
name = "test-project"
dependencies = ["requests>=2.0.0", "click"]

[tool.poetry.dependencies]
python = "^3.8"
fastapi = "^0.68.0"
""")
            (project_path / "main.py").write_text("print('Hello World')")
            (project_path / "src").mkdir()
            (project_path / "src" / "app.py").write_text("from fastapi import FastAPI")

            analyzer = ContextAnalyzer(project_path)
            context = analyzer.analyze()

            assert context.project_type == ProjectType.PYTHON
            assert context.framework == FrameworkType.FASTAPI
            assert context.total_files >= 3
            assert context.code_files >= 2
            assert len(context.dependencies) >= 2
            assert any(dep.name == "fastapi" for dep in context.dependencies)
            assert "poetry" in context.build_tools

    def test_javascript_project_detection(self):
        """Test detection of JavaScript projects"""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)

            # Create JavaScript project files
            package_json = {
                "name": "test-project",
                "dependencies": {"react": "^18.0.0", "express": "^4.18.0"},
                "devDependencies": {"jest": "^29.0.0"},
            }
            (project_path / "package.json").write_text(json.dumps(package_json))
            (project_path / "index.js").write_text("const express = require('express');")
            (project_path / "src").mkdir()
            (project_path / "src" / "App.js").write_text("import React from 'react';")

            analyzer = ContextAnalyzer(project_path)
            context = analyzer.analyze()

            assert context.project_type == ProjectType.JAVASCRIPT
            assert context.framework in [FrameworkType.REACT, FrameworkType.EXPRESS]
            assert len(context.dependencies) >= 3
            assert any(dep.name == "react" for dep in context.dependencies)
            assert any(dep.dev_dependency for dep in context.dependencies)
            assert "npm" in context.build_tools
            assert "jest" in context.test_frameworks

    def test_nix_project_detection(self):
        """Test detection of Nix projects"""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)

            # Create Nix project files
            (project_path / "flake.nix").write_text("""
{
  description = "Test flake";
  inputs.nixpkgs.url = "github:NixOS/nixpkgs";
}
""")
            (project_path / "shell.nix").write_text("{ pkgs ? import <nixpkgs> {} }: pkgs.mkShell {}")
            (project_path / "default.nix").write_text("{ pkgs }: pkgs.hello")

            analyzer = ContextAnalyzer(project_path)
            context = analyzer.analyze()

            assert context.project_type == ProjectType.NIX
            assert "nix" in context.build_tools

    def test_mixed_project_detection(self):
        """Test detection of mixed-language projects"""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)

            # Create mixed project files
            (project_path / "package.json").write_text('{"name": "test"}')
            (project_path / "pyproject.toml").write_text('[project]\nname = "test"')
            (project_path / "Cargo.toml").write_text('[package]\nname = "test"')
            (project_path / "main.py").write_text("print('Python')")
            (project_path / "index.js").write_text("console.log('JS');")
            (project_path / "main.rs").write_text('fn main() { println!("Rust"); }')

            analyzer = ContextAnalyzer(project_path)
            context = analyzer.analyze()

            assert context.project_type == ProjectType.MIXED
            assert len(context.build_tools) >= 2

    def test_complexity_calculation(self):
        """Test complexity score calculation"""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)

            # Create simple project
            (project_path / "main.py").write_text("print('Hello')")

            analyzer = ContextAnalyzer(project_path)
            context = analyzer.analyze()
            simple_complexity = context.complexity_score

            # Add more complexity
            (project_path / "requirements.txt").write_text("requests\nclick\nnumpy\npandas\ndjango")
            (project_path / "src").mkdir()
            (project_path / "src" / "deep").mkdir()
            (project_path / "src" / "deep" / "nested").mkdir()
            (project_path / "src" / "deep" / "nested" / "file.py").write_text("# Deep file")

            for i in range(20):
                (project_path / f"file_{i}.py").write_text(f"# File {i}")

            analyzer = ContextAnalyzer(project_path)
            context = analyzer.analyze()
            complex_complexity = context.complexity_score

            assert complex_complexity > simple_complexity
            assert 0 <= context.complexity_score <= 254

    def test_dependency_parsing(self):
        """Test dependency parsing from various sources"""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)

            # Test requirements.txt parsing
            (project_path / "requirements.txt").write_text("""
requests>=2.25.0
click==8.0.0
# This is a comment
numpy~=1.21.0
pandas
""")

            analyzer = ContextAnalyzer(project_path)
            context = analyzer.analyze()

            dep_names = [dep.name for dep in context.dependencies]
            assert "requests" in dep_names
            assert "click" in dep_names
            assert "numpy" in dep_names
            assert "pandas" in dep_names

            # Check version parsing
            requests_dep = next(dep for dep in context.dependencies if dep.name == "requests")
            assert requests_dep.version == ">=2.25.0"

    def test_entry_point_detection(self):
        """Test entry point detection"""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)

            # Create entry points
            (project_path / "main.py").write_text("if __name__ == '__main__':")
            (project_path / "app.py").write_text("from flask import Flask")
            (project_path / "src").mkdir()
            (project_path / "src" / "main.py").write_text("def main():")

            analyzer = ContextAnalyzer(project_path)
            context = analyzer.analyze()

            assert len(context.entry_points) >= 2
            assert any("main.py" in entry for entry in context.entry_points)
            assert any("app.py" in entry for entry in context.entry_points)

    def test_key_directories_detection(self):
        """Test key directory detection"""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)

            # Create key directories
            (project_path / "src").mkdir()
            (project_path / "tests").mkdir()
            (project_path / "docs").mkdir()
            (project_path / "config").mkdir()
            (project_path / "random_dir").mkdir()

            analyzer = ContextAnalyzer(project_path)
            context = analyzer.analyze()

            assert "src" in context.key_directories
            assert "tests" in context.key_directories
            assert "docs" in context.key_directories
            assert "config" in context.key_directories
            # random_dir should not be included as it's not a known key directory

    def test_file_type_counting(self):
        """Test accurate file type counting"""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)

            # Create various file types
            (project_path / "main.py").write_text("# Python code")
            (project_path / "script.js").write_text("// JavaScript code")
            (project_path / "config.json").write_text('{"key": "value"}')
            (project_path / "settings.yaml").write_text("key: value")
            (project_path / "README.md").write_text("# Documentation")
            (project_path / "data.txt").write_text("Some data")

            analyzer = ContextAnalyzer(project_path)
            context = analyzer.analyze()

            assert context.code_files >= 2  # main.py, script.js
            assert context.config_files >= 2  # config.json, settings.yaml
            assert context.total_files >= 6

    def test_error_handling(self):
        """Test error handling for invalid inputs"""
        # Test non-existent directory
        with pytest.raises(FileNotFoundError):
            ContextAnalyzer(Path("/non/existent/path"))

        # Test file instead of directory
        with tempfile.NamedTemporaryFile() as temp_file:
            with pytest.raises(NotADirectoryError):
                ContextAnalyzer(Path(temp_file.name))

    def test_to_dict_serialization(self):
        """Test JSON serialization of results"""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            (project_path / "main.py").write_text("print('Hello')")

            analyzer = ContextAnalyzer(project_path)
            context = analyzer.analyze()

            # Test serialization
            context_dict = context.to_dict()
            assert isinstance(context_dict, dict)
            assert "project_type" in context_dict
            assert "framework" in context_dict
            assert "complexity_score" in context_dict
            assert "dependencies" in context_dict

            # Test that it's JSON serializable
            json_str = json.dumps(context_dict)
            assert isinstance(json_str, str)

            # Test dependency serialization
            if context.dependencies:
                dep_dict = context.dependencies[0].to_dict()
                assert isinstance(dep_dict, dict)
                assert "name" in dep_dict
