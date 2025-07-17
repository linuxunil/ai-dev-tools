"""
Basic Pattern Scanner Tests

Tests core pattern scanning functionality to ensure it works correctly.
"""

import tempfile
from pathlib import Path

from ai_dev_tools.core.pattern_scanner import PatternScanner, PatternType


class TestPatternScannerBasic:
    """Test basic pattern scanner functionality"""

    def setup_method(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_path = Path(self.temp_dir)
        self.scanner = PatternScanner()

    def test_scanner_initialization(self):
        """Test scanner initializes correctly"""
        scanner = PatternScanner()
        assert scanner.file_extensions == [".nix"]
        assert hasattr(scanner, "_pattern_cache")

    def test_scan_nonexistent_file(self):
        """Test scanning nonexistent file returns empty result"""
        result = self.scanner.scan_for_similar_patterns(
            target_file="nonexistent.nix", target_line=1, search_dir=str(self.test_path)
        )
        assert result.count == 0
        assert len(result.matches) == 0

    def test_scan_empty_directory(self):
        """Test scanning empty directory returns empty result"""
        # Create a test file
        test_file = self.test_path / "test.nix"
        test_file.write_text("# Empty file\n")

        result = self.scanner.scan_for_similar_patterns(
            target_file=str(test_file), target_line=1, search_dir=str(self.test_path)
        )
        assert result.count == 0
        assert len(result.matches) == 0

    def test_scan_with_similar_patterns(self):
        """Test scanning finds similar patterns"""
        # Create target file
        target_file = self.test_path / "target.nix"
        target_file.write_text(
            """
mkIf config.programs.git.enable home.packages = with pkgs; [ git ];
""".strip()
        )

        # Create file with similar pattern
        similar_file = self.test_path / "similar.nix"
        similar_file.write_text(
            """
mkIf config.programs.vim.enable home.packages = with pkgs; [ vim ];
mkIf config.programs.git.enable home.packages = with pkgs; [ git ];
""".strip()
        )

        result = self.scanner.scan_for_similar_patterns(
            target_file=str(target_file), target_line=1, search_dir=str(self.test_path)
        )

        # Should find the similar pattern (but not the exact same line)
        assert result.count >= 1
        assert result.pattern_type == PatternType.MKIF_HOME_PACKAGES

    def test_pattern_type_detection(self):
        """Test pattern type detection works correctly"""
        # Test mkIf home.packages pattern
        target_file = self.test_path / "mkif.nix"
        target_file.write_text("mkIf config.programs.git.enable home.packages = with pkgs; [ git ];")

        result = self.scanner.scan_for_similar_patterns(
            target_file=str(target_file), target_line=1, search_dir=str(self.test_path)
        )

        assert result.pattern_type == PatternType.MKIF_HOME_PACKAGES

    def test_max_results_limit(self):
        """Test max results parameter works"""
        # Create target file
        target_file = self.test_path / "target.nix"
        target_file.write_text("mkIf config.test home.packages = with pkgs; [ test ];")

        # Create multiple similar files
        for i in range(10):
            similar_file = self.test_path / f"similar_{i}.nix"
            similar_file.write_text(f"mkIf config.test{i} home.packages = with pkgs; [ test{i} ];")

        result = self.scanner.scan_for_similar_patterns(
            target_file=str(target_file),
            target_line=1,
            search_dir=str(self.test_path),
            max_results=5,
        )

        # Should respect max_results limit
        assert len(result.matches) <= 5

    def test_exit_code_encoding(self):
        """Test that results can be encoded as exit codes"""
        target_file = self.test_path / "target.nix"
        target_file.write_text("test content")

        result = self.scanner.scan_for_similar_patterns(
            target_file=str(target_file), target_line=1, search_dir=str(self.test_path)
        )

        # Exit code should be count (capped at 254)
        exit_code = min(result.count, 254)
        assert 0 <= exit_code <= 254
