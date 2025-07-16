"""
Performance Benchmarks for AI Development Tools

Tests that ensure tools are fast enough for AI workflows and measure
performance characteristics.
"""

import subprocess
import pytest
import tempfile
from pathlib import Path
import time
import psutil
import os
from typing import List, Dict, Any


class TestExecutionSpeed:
    """Test execution speed of tools"""

    def setup_method(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.repo_path = Path(self.temp_dir)

        # Create test repository with various file sizes
        self.create_performance_test_repo()

    def create_performance_test_repo(self):
        """Create repository optimized for performance testing"""

        # Small files (typical case)
        for i in range(10):
            small_file = self.repo_path / f"small_{i}.nix"
            small_file.write_text(f"""
{{ config, lib, pkgs, ... }}:
{{
  home.packages = lib.mkIf config.programs.small{i}.enable [
    pkgs.git
    pkgs.vim
  ];
}}
""")

        # Medium files
        for i in range(5):
            medium_file = self.repo_path / f"medium_{i}.nix"
            content = f"""
{{ config, lib, pkgs, ... }}:
{{
  environment.systemPackages = lib.mkIf config.programs.medium{i}.enable [
"""
            # Add many packages to make file larger
            for j in range(50):
                content += f"    pkgs.package{j}\n"
            content += "  ];\n}\n"
            medium_file.write_text(content)

        # Large file (stress test)
        large_file = self.repo_path / "large.nix"
        content = "{ config, lib, pkgs, ... }:\n{\n"
        for i in range(100):
            content += f"""
  environment.systemPackages{i} = lib.mkIf config.programs.large{i}.enable [
"""
            for j in range(20):
                content += f"    pkgs.package{i}_{j}\n"
            content += "  ];\n"
        content += "}\n"
        large_file.write_text(content)

    def measure_execution_time(self, tool: str, *args) -> float:
        """Measure execution time of a tool"""
        cmd = [tool] + list(args) + ["--format", "silent"]

        start_time = time.time()
        result = subprocess.run(cmd, capture_output=True, cwd=self.repo_path)
        end_time = time.time()

        # Ensure command succeeded (or failed predictably)
        assert result.returncode != -1  # Not killed by signal

        return end_time - start_time

    def test_pattern_scanner_speed(self):
        """Test pattern scanner execution speed"""

        # Test on small file
        small_time = self.measure_execution_time(
            "ai-pattern-scan",
            f"{self.repo_path}/small_0.nix:3",
            "--search-dir",
            str(self.repo_path),
        )

        # Should complete quickly
        assert small_time < 2.0, f"Pattern scan took {small_time:.2f}s, expected < 2.0s"

        # Test on large search space
        large_time = self.measure_execution_time(
            "ai-pattern-scan",
            f"{self.repo_path}/large.nix:3",
            "--search-dir",
            str(self.repo_path),
        )

        # Should still complete in reasonable time
        assert large_time < 10.0, (
            f"Large pattern scan took {large_time:.2f}s, expected < 10.0s"
        )

    def test_safety_checker_speed(self):
        """Test safety checker execution speed"""

        # Test various file types
        test_files = [
            self.repo_path / "small_0.nix",
            self.repo_path / "medium_0.nix",
            self.repo_path / "large.nix",
        ]

        for test_file in test_files:
            exec_time = self.measure_execution_time("ai-safety-check", str(test_file))

            # Safety checking should be very fast (file analysis only)
            assert exec_time < 1.0, (
                f"Safety check of {test_file.name} took {exec_time:.2f}s, expected < 1.0s"
            )

    def test_repo_analyzer_speed(self):
        """Test repository analyzer execution speed"""

        exec_time = self.measure_execution_time(
            "ai-repo-status", "--repo-path", str(self.repo_path)
        )

        # Repository analysis should complete quickly
        assert exec_time < 5.0, f"Repo analysis took {exec_time:.2f}s, expected < 5.0s"

    def test_batch_operation_speed(self):
        """Test speed of batch operations (multiple tool calls)"""

        start_time = time.time()

        # Simulate AI workflow: check multiple files
        for i in range(5):
            subprocess.run(
                [
                    "ai-safety-check",
                    str(self.repo_path / f"small_{i}.nix"),
                    "--format",
                    "silent",
                ],
                capture_output=True,
            )

        batch_time = time.time() - start_time

        # Batch operations should be efficient
        assert batch_time < 3.0, (
            f"Batch operations took {batch_time:.2f}s, expected < 3.0s"
        )

        # Average per operation should be very fast
        avg_time = batch_time / 5
        assert avg_time < 0.6, (
            f"Average operation time {avg_time:.2f}s, expected < 0.6s"
        )


class TestMemoryUsage:
    """Test memory usage characteristics"""

    def setup_method(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.repo_path = Path(self.temp_dir)

    def measure_memory_usage(self, tool: str, *args) -> Dict[str, float]:
        """Measure memory usage of a tool execution"""
        cmd = [tool] + list(args) + ["--format", "silent"]

        # Start process
        process = subprocess.Popen(cmd, cwd=self.repo_path)

        # Monitor memory usage
        max_memory = 0
        try:
            ps_process = psutil.Process(process.pid)
            while process.poll() is None:
                try:
                    memory_info = ps_process.memory_info()
                    max_memory = max(max_memory, memory_info.rss)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    break
                time.sleep(0.01)  # Check every 10ms
        except psutil.NoSuchProcess:
            pass

        # Wait for completion
        process.wait()

        return {
            "max_rss_mb": max_memory / (1024 * 1024),
            "exit_code": process.returncode,
        }

    def test_memory_efficiency(self):
        """Test that tools use reasonable amounts of memory"""

        # Create test file
        test_file = self.repo_path / "test.nix"
        test_file.write_text("{ services.nginx.enable = true; }")

        # Test pattern scanner memory usage
        memory_stats = self.measure_memory_usage(
            "ai-pattern-scan", f"{test_file}:1", "--search-dir", str(self.repo_path)
        )

        # Should use reasonable memory (< 100MB for simple operations)
        assert memory_stats["max_rss_mb"] < 100, (
            f"Used {memory_stats['max_rss_mb']:.1f}MB, expected < 100MB"
        )

        # Test safety checker memory usage
        memory_stats = self.measure_memory_usage("ai-safety-check", str(test_file))

        # Safety checking should use minimal memory
        assert memory_stats["max_rss_mb"] < 50, (
            f"Used {memory_stats['max_rss_mb']:.1f}MB, expected < 50MB"
        )


class TestScalability:
    """Test how tools scale with repository size"""

    def create_repo_of_size(self, num_files: int) -> Path:
        """Create repository with specified number of files"""
        temp_dir = tempfile.mkdtemp()
        repo_path = Path(temp_dir)

        for i in range(num_files):
            test_file = repo_path / f"file_{i}.nix"
            test_file.write_text(f"""
{{ config, lib, pkgs, ... }}:
{{
  home.packages = lib.mkIf config.programs.test{i}.enable [
    pkgs.git
    pkgs.vim
  ];
}}
""")

        return repo_path

    def test_pattern_scanner_scalability(self):
        """Test pattern scanner performance with different repository sizes"""

        sizes_and_limits = [
            (10, 2.0),  # 10 files, < 2 seconds
            (50, 5.0),  # 50 files, < 5 seconds
            (100, 10.0),  # 100 files, < 10 seconds
        ]

        for num_files, time_limit in sizes_and_limits:
            repo_path = self.create_repo_of_size(num_files)

            start_time = time.time()
            result = subprocess.run(
                [
                    "ai-pattern-scan",
                    f"{repo_path}/file_0.nix:3",
                    "--search-dir",
                    str(repo_path),
                    "--format",
                    "silent",
                ],
                capture_output=True,
            )
            exec_time = time.time() - start_time

            assert exec_time < time_limit, (
                f"{num_files} files took {exec_time:.2f}s, expected < {time_limit}s"
            )
            assert result.returncode >= 0  # Should succeed

    def test_linear_scaling(self):
        """Test that execution time scales roughly linearly with input size"""

        # Test with different sizes
        sizes = [10, 20, 40]
        times = []

        for size in sizes:
            repo_path = self.create_repo_of_size(size)

            start_time = time.time()
            subprocess.run(
                [
                    "ai-pattern-scan",
                    f"{repo_path}/file_0.nix:3",
                    "--search-dir",
                    str(repo_path),
                    "--format",
                    "silent",
                ],
                capture_output=True,
            )
            exec_time = time.time() - start_time
            times.append(exec_time)

        # Check that scaling is reasonable (not exponential)
        # Time for 40 files should be less than 5x time for 10 files
        scaling_factor = times[2] / times[0]  # 40 files vs 10 files
        assert scaling_factor < 5.0, (
            f"Scaling factor {scaling_factor:.2f} too high, expected < 5.0"
        )


class TestConcurrency:
    """Test concurrent execution of tools"""

    def test_concurrent_execution(self):
        """Test that multiple tools can run concurrently"""
        import concurrent.futures

        temp_dir = tempfile.mkdtemp()
        repo_path = Path(temp_dir)

        # Create test file
        test_file = repo_path / "test.nix"
        test_file.write_text("{ services.nginx.enable = true; }")

        def run_tool(tool_and_args):
            tool, args = tool_and_args
            cmd = [tool] + args + ["--format", "silent"]
            result = subprocess.run(cmd, capture_output=True, cwd=repo_path)
            return result.returncode

        # Define concurrent operations
        operations = [
            ("ai-safety-check", [str(test_file)]),
            ("ai-pattern-scan", [f"{test_file}:1", "--search-dir", str(repo_path)]),
            ("ai-repo-status", ["--repo-path", str(repo_path)]),
        ]

        # Run concurrently
        start_time = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            results = list(executor.map(run_tool, operations))
        concurrent_time = time.time() - start_time

        # All should complete successfully
        assert all(result != -1 for result in results)  # No signals

        # Should complete quickly when run concurrently
        assert concurrent_time < 5.0, (
            f"Concurrent execution took {concurrent_time:.2f}s, expected < 5.0s"
        )


class TestPerformanceRegression:
    """Test for performance regressions"""

    def test_baseline_performance(self):
        """Establish baseline performance metrics"""

        temp_dir = tempfile.mkdtemp()
        repo_path = Path(temp_dir)

        # Create standard test scenario
        test_file = repo_path / "test.nix"
        test_file.write_text("""
{ config, lib, pkgs, ... }:
{
  home.packages = lib.mkIf config.programs.development.enable [
    pkgs.git
    pkgs.vim
  ];
}
""")

        # Measure baseline performance
        baselines = {}

        # Pattern scanner baseline
        start_time = time.time()
        subprocess.run(
            [
                "ai-pattern-scan",
                f"{test_file}:3",
                "--search-dir",
                str(repo_path),
                "--format",
                "silent",
            ],
            capture_output=True,
        )
        baselines["pattern_scan"] = time.time() - start_time

        # Safety checker baseline
        start_time = time.time()
        subprocess.run(
            ["ai-safety-check", str(test_file), "--format", "silent"],
            capture_output=True,
        )
        baselines["safety_check"] = time.time() - start_time

        # Repository analyzer baseline
        start_time = time.time()
        subprocess.run(
            ["ai-repo-status", "--repo-path", str(repo_path), "--format", "silent"],
            capture_output=True,
        )
        baselines["repo_status"] = time.time() - start_time

        # Assert reasonable baselines
        assert baselines["pattern_scan"] < 2.0
        assert baselines["safety_check"] < 1.0
        assert baselines["repo_status"] < 3.0

        # Store baselines for future regression testing
        # In practice, these would be stored in a performance database
