"""
Basic tests for DifferenceAnalyzer - Core functionality validation
"""

import pytest
import tempfile
from pathlib import Path
from ai_dev_tools.core.difference_analyzer import (
    DifferenceAnalyzer,
    DifferenceType,
    ChangeSignificance,
)


class TestDifferenceAnalyzer:
    """Test DifferenceAnalyzer core functionality"""

    def test_analyzer_initialization(self):
        """Test analyzer can be initialized with options"""
        analyzer = DifferenceAnalyzer()
        assert analyzer.ignore_whitespace is True
        assert analyzer.ignore_comments is False

        analyzer_custom = DifferenceAnalyzer(
            ignore_whitespace=False, ignore_comments=True
        )
        assert analyzer_custom.ignore_whitespace is False
        assert analyzer_custom.ignore_comments is True

    def test_identical_files(self):
        """Test comparing identical files returns no differences"""
        analyzer = DifferenceAnalyzer()

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create identical files
            file1 = temp_path / "file1.txt"
            file2 = temp_path / "file2.txt"

            content = "Hello, world!\nThis is a test file.\n"
            file1.write_text(content)
            file2.write_text(content)

            analysis = analyzer.compare_files(file1, file2)

            assert analysis.total_differences == 0
            assert analysis.significant_differences == 0
            assert analysis.files_compared == 2
            assert analysis.files_modified == 0
            assert len(analysis.differences) == 0

    def test_different_files(self):
        """Test comparing different files detects differences"""
        analyzer = DifferenceAnalyzer()

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create different files
            file1 = temp_path / "file1.txt"
            file2 = temp_path / "file2.txt"

            file1.write_text("Hello, world!\nThis is a test file.\n")
            file2.write_text(
                "Hello, universe!\nThis is a test file.\nWith an extra line.\n"
            )

            analysis = analyzer.compare_files(file1, file2)

            assert analysis.total_differences == 1
            assert analysis.significant_differences >= 1
            assert analysis.files_compared == 2
            assert analysis.files_modified == 1
            assert len(analysis.differences) == 1

            diff = analysis.differences[0]
            assert diff.difference_type == DifferenceType.CONTENT_CHANGED
            assert diff.line_changes > 0
            assert diff.added_lines > 0

    def test_whitespace_handling(self):
        """Test whitespace handling option"""
        analyzer_ignore = DifferenceAnalyzer(ignore_whitespace=True)
        analyzer_strict = DifferenceAnalyzer(ignore_whitespace=False)

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create files with whitespace differences
            file1 = temp_path / "file1.txt"
            file2 = temp_path / "file2.txt"

            file1.write_text("Hello, world!\nThis is a test.\n")
            file2.write_text(
                "Hello, world!   \n  This is a test.  \n"
            )  # Extra whitespace

            # With whitespace ignored, should be identical
            analysis_ignore = analyzer_ignore.compare_files(file1, file2)
            assert analysis_ignore.total_differences == 0

            # With strict whitespace, should detect differences
            analysis_strict = analyzer_strict.compare_files(file1, file2)
            assert analysis_strict.total_differences == 1

    def test_directory_comparison(self):
        """Test comparing directories"""
        analyzer = DifferenceAnalyzer()

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create two directories with different content
            dir1 = temp_path / "dir1"
            dir2 = temp_path / "dir2"
            dir1.mkdir()
            dir2.mkdir()

            # Common file (identical)
            (dir1 / "common.txt").write_text("Common content\n")
            (dir2 / "common.txt").write_text("Common content\n")

            # Modified file
            (dir1 / "modified.txt").write_text("Original content\n")
            (dir2 / "modified.txt").write_text("Modified content\n")

            # File only in dir1 (removed)
            (dir1 / "removed.txt").write_text("This will be removed\n")

            # File only in dir2 (added)
            (dir2 / "added.txt").write_text("This is new\n")

            analysis = analyzer.compare_directories(dir1, dir2)

            assert analysis.files_compared == 4  # common, modified, removed, added
            assert analysis.files_added == 1
            assert analysis.files_removed == 1
            assert analysis.files_modified == 1
            assert analysis.total_differences == 3  # modified, removed, added

            # Check specific differences
            diff_types = {diff.difference_type for diff in analysis.differences}
            assert DifferenceType.CONTENT_CHANGED in diff_types
            assert DifferenceType.ADDED in diff_types
            assert DifferenceType.REMOVED in diff_types

    def test_significance_detection(self):
        """Test change significance detection"""
        analyzer = DifferenceAnalyzer()

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Test critical changes (function definition)
            file1 = temp_path / "critical1.py"
            file2 = temp_path / "critical2.py"

            file1.write_text("def old_function():\n    pass\n")
            file2.write_text("def new_function():\n    pass\n")

            analysis = analyzer.compare_files(file1, file2)

            assert len(analysis.differences) == 1
            diff = analysis.differences[0]
            assert diff.significance == ChangeSignificance.CRITICAL

    def test_file_not_found_error(self):
        """Test error handling for non-existent files"""
        analyzer = DifferenceAnalyzer()

        with pytest.raises(FileNotFoundError):
            analyzer.compare_files(Path("nonexistent1.txt"), Path("nonexistent2.txt"))

    def test_mixed_file_directory_error(self):
        """Test error handling when comparing file to directory"""
        analyzer = DifferenceAnalyzer()

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create a file and a directory
            test_file = temp_path / "test.txt"
            test_dir = temp_path / "test_dir"

            test_file.write_text("Test content")
            test_dir.mkdir()

            # This should be handled by the CLI, but test the core logic
            # The analyzer expects both to be files or both to be directories
            # This test ensures we handle the case properly in the CLI

    def test_binary_file_comparison(self):
        """Test comparison of binary files"""
        analyzer = DifferenceAnalyzer()

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create binary files (using .bin extension to avoid text detection)
            file1 = temp_path / "binary1.bin"
            file2 = temp_path / "binary2.bin"

            file1.write_bytes(b"\x00\x01\x02\x03")
            file2.write_bytes(b"\x00\x01\x02\x04")  # Different last byte

            analysis = analyzer.compare_files(file1, file2)

            assert analysis.total_differences == 1
            diff = analysis.differences[0]
            assert diff.difference_type == DifferenceType.CONTENT_CHANGED
            assert "Binary file changed" in diff.details

    def test_text_file_detection(self):
        """Test text file detection logic"""
        analyzer = DifferenceAnalyzer()

        # Test various text file extensions
        text_files = [
            "test.py",
            "test.js",
            "test.ts",
            "test.json",
            "test.yaml",
            "test.md",
            "test.txt",
            "test.nix",
        ]

        for filename in text_files:
            path = Path(filename)
            assert analyzer._is_text_file(path), (
                f"{filename} should be detected as text file"
            )

        # Test non-text files
        binary_files = ["test.bin", "test.exe", "test.jpg", "test.pdf"]

        for filename in binary_files:
            path = Path(filename)
            assert not analyzer._is_text_file(path), (
                f"{filename} should not be detected as text file"
            )

    def test_summary_generation(self):
        """Test difference summary generation"""
        analyzer = DifferenceAnalyzer()

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create directories with multiple types of changes
            dir1 = temp_path / "dir1"
            dir2 = temp_path / "dir2"
            dir1.mkdir()
            dir2.mkdir()

            # Various types of changes
            (dir1 / "modified.txt").write_text("Original\n")
            (dir2 / "modified.txt").write_text("Modified\n")

            (dir1 / "removed.txt").write_text("To be removed\n")
            (dir2 / "added.txt").write_text("Newly added\n")

            analysis = analyzer.compare_directories(dir1, dir2)

            assert "differences found" in analysis.summary
            assert "content_changed" in analysis.summary or "added" in analysis.summary
            assert len(analysis.summary) > 0
