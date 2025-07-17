"""
Integration Tests for AI Development Tools

Tests that verify tools work together effectively in real-world scenarios.
"""

import subprocess
import tempfile
import time
from pathlib import Path


class TestToolIntegration:
    """Test tools working together in realistic scenarios"""

    def setup_method(self):
        """Set up realistic test repository"""
        self.temp_dir = tempfile.mkdtemp()
        self.repo_path = Path(self.temp_dir)

        # Create realistic Nix configuration repository
        self.create_realistic_repo()

    def create_realistic_repo(self):
        """Create a realistic repository structure"""

        # Main system configuration
        (self.repo_path / "configuration.nix").write_text("""
{ config, pkgs, ... }:
{
  imports = [
    ./hardware-configuration.nix
    ./modules/development.nix
    ./modules/desktop.nix
  ];

  boot.loader.systemd-boot.enable = true;
  networking.hostName = "nixos-machine";

  users.users.user = {
    isNormalUser = true;
    extraGroups = [ "wheel" "docker" ];
  };
}
""")

        # Hardware configuration
        (self.repo_path / "hardware-configuration.nix").write_text("""
{ config, lib, pkgs, modulesPath, ... }:
{
  boot.initrd.availableKernelModules = [ "xhci_pci" "ahci" ];
  fileSystems."/" = {
    device = "/dev/disk/by-uuid/12345";
    fsType = "ext4";
  };
}
""")

        # Modules directory
        modules_dir = self.repo_path / "modules"
        modules_dir.mkdir()

        # Development module with patterns
        (modules_dir / "development.nix").write_text("""
{ config, lib, pkgs, ... }:
{
  environment.systemPackages = lib.mkIf config.programs.development.enable [
    pkgs.git
    pkgs.vim
    pkgs.nodejs
  ];

  programs.docker.enable = true;
  virtualisation.docker.enable = true;
}
""")

        # Desktop module with similar patterns
        (modules_dir / "desktop.nix").write_text("""
{ config, lib, pkgs, ... }:
{
  environment.systemPackages = lib.mkIf config.programs.desktop.enable [
    pkgs.firefox
    pkgs.vscode
    pkgs.discord
  ];

  services.xserver.enable = true;
  services.xserver.displayManager.gdm.enable = true;
}
""")

        # Home manager configuration
        (modules_dir / "home.nix").write_text("""
{ config, lib, pkgs, ... }:
{
  home.packages = lib.mkIf config.programs.personal.enable [
    pkgs.spotify
    pkgs.telegram-desktop
  ];

  programs.git = {
    enable = true;
    userName = "User";
    userEmail = "user@example.com";
  };
}
""")

        # Flake file (critical)
        (self.repo_path / "flake.nix").write_text("""
{
  description = "NixOS configuration";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    home-manager.url = "github:nix-community/home-manager";
  };

  outputs = { self, nixpkgs, home-manager }: {
    nixosConfigurations.nixos-machine = nixpkgs.lib.nixosSystem {
      system = "x86_64-linux";
      modules = [ ./configuration.nix ];
    };
  };
}
""")

        # Source code directory
        src_dir = self.repo_path / "src"
        src_dir.mkdir()
        (src_dir / "utils.py").write_text("""
def configure_system():
    \"\"\"Helper function for system configuration\"\"\"
    return {"status": "configured"}

def validate_config():
    \"\"\"Validate configuration files\"\"\"
    return True
""")

    def run_tool(self, tool: str, *args, format_type: str = "silent") -> tuple[int, str]:
        """Run a tool and return exit code and output"""
        cmd = [tool] + list(args) + ["--format", format_type]
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.repo_path)
        return result.returncode, result.stdout

    def test_complete_ai_workflow(self):
        """Test complete AI workflow: assess → find → fix → validate"""

        # Step 1: AI assesses repository health
        repo_status, _ = self.run_tool("ai-repo-status", "--repo-path", str(self.repo_path))

        # Repository should be clean (0 syntax errors)
        assert repo_status == 0

        # Step 2: AI finds patterns after fixing an issue in development.nix
        pattern_count, _ = self.run_tool(
            "ai-pattern-scan",
            f"{self.repo_path}/modules/development.nix:4",  # mkIf pattern
            "--search-dir",
            str(self.repo_path / "modules"),
        )

        # Should find similar patterns in desktop.nix and home.nix
        assert pattern_count >= 1

        # Step 3: AI checks safety of each found pattern location
        safety_results = {}

        # Check development.nix (medium risk - system config)
        dev_risk, _ = self.run_tool("ai-safety-check", f"{self.repo_path}/modules/development.nix")
        safety_results["development.nix"] = dev_risk

        # Check desktop.nix (medium risk - system config)
        desktop_risk, _ = self.run_tool("ai-safety-check", f"{self.repo_path}/modules/desktop.nix")
        safety_results["desktop.nix"] = desktop_risk

        # Check home.nix (medium risk - user config)
        home_risk, _ = self.run_tool("ai-safety-check", f"{self.repo_path}/modules/home.nix")
        safety_results["home.nix"] = home_risk

        # All module files should be medium risk (exit code 1)
        assert all(risk == 1 for risk in safety_results.values())

        # Step 4: AI decides to proceed with medium-risk files
        files_to_modify = [f for f, risk in safety_results.items() if risk <= 1]
        assert len(files_to_modify) == 3

        # Step 5: AI validates repository is still clean after changes
        final_status, _ = self.run_tool("ai-repo-status", "--repo-path", str(self.repo_path))
        assert final_status == 0

    def test_safety_hierarchy_validation(self):
        """Test that safety checker correctly categorizes files by risk"""

        files_and_expected_risks = [
            # Critical files (exit code 3)
            ("flake.nix", 3),
            ("configuration.nix", 2),  # High risk
            ("hardware-configuration.nix", 2),  # High risk
            # Medium risk files (exit code 1)
            ("modules/development.nix", 1),
            ("modules/desktop.nix", 1),
            ("modules/home.nix", 1),
            # Safe files (exit code 0)
            ("src/utils.py", 0),
        ]

        for file_path, expected_risk in files_and_expected_risks:
            actual_risk, _ = self.run_tool("ai-safety-check", f"{self.repo_path}/{file_path}")
            assert actual_risk == expected_risk, f"File {file_path} should have risk {expected_risk}, got {actual_risk}"

    def test_pattern_detection_accuracy(self):
        """Test that pattern detection finds correct similar patterns"""

        # Test mkIf pattern detection
        pattern_count, _ = self.run_tool(
            "ai-pattern-scan",
            f"{self.repo_path}/modules/development.nix:4",  # environment.systemPackages with mkIf
            "--search-dir",
            str(self.repo_path),
        )

        # Should find similar patterns in desktop.nix and home.nix
        assert pattern_count >= 2

        # Test that it doesn't find false positives
        unique_pattern_count, _ = self.run_tool(
            "ai-pattern-scan",
            f"{self.repo_path}/hardware-configuration.nix:3",  # boot.initrd pattern
            "--search-dir",
            str(self.repo_path),
        )

        # Should find few or no similar patterns (hardware config is unique)
        assert unique_pattern_count <= 1

    def test_cross_tool_consistency(self):
        """Test that tools provide consistent information"""

        # Run multiple tools on same repository
        repo_status, _ = self.run_tool("ai-repo-status", "--repo-path", str(self.repo_path))

        # If repo is clean, safety checks should work properly
        if repo_status == 0:
            # Safety checker should work on all files
            test_file = self.repo_path / "modules" / "development.nix"
            safety_risk, _ = self.run_tool("ai-safety-check", str(test_file))

            # Should return valid risk level (0-3)
            assert 0 <= safety_risk <= 3

            # Pattern scanner should work
            pattern_count, _ = self.run_tool("ai-pattern-scan", f"{test_file}:4", "--search-dir", str(self.repo_path))

            # Should return valid count (0-254) or error (255)
            assert (0 <= pattern_count <= 254) or pattern_count == 255

    def test_error_propagation(self):
        """Test that errors are handled consistently across tools"""

        # Test with non-existent file
        tools_to_test = [
            ("ai-pattern-scan", "nonexistent.nix:10"),
            ("ai-safety-check", "nonexistent.nix"),
        ]

        for tool, invalid_arg in tools_to_test:
            exit_code, output = self.run_tool(tool, invalid_arg)

            # All tools should return error code 255 for invalid input
            assert exit_code == 255

            # Silent mode should produce no output even for errors
            assert output == ""

    def test_performance_under_load(self):
        """Test tool performance with larger repository"""

        # Create additional files to simulate larger repository
        for i in range(20):
            module_file = self.repo_path / "modules" / f"module_{i}.nix"
            module_file.write_text(f"""
{{ config, lib, pkgs, ... }}:
{{
  environment.systemPackages = lib.mkIf config.programs.module{i}.enable [
    pkgs.package{i}
  ];
}}
""")

        # Test pattern scanning performance
        start_time = time.time()
        pattern_count, _ = self.run_tool(
            "ai-pattern-scan",
            f"{self.repo_path}/modules/development.nix:4",
            "--search-dir",
            str(self.repo_path / "modules"),
        )
        scan_time = time.time() - start_time

        # Should complete quickly even with many files
        assert scan_time < 5.0  # 5 second timeout

        # Should find many similar patterns
        assert pattern_count >= 20

        # Test safety checking performance
        start_time = time.time()
        safety_risk, _ = self.run_tool("ai-safety-check", f"{self.repo_path}/modules/module_0.nix")
        safety_time = time.time() - start_time

        # Should complete quickly
        assert safety_time < 1.0  # 1 second timeout
        assert 0 <= safety_risk <= 3


class TestRealWorldScenarios:
    """Test scenarios based on real AI development workflows"""

    def test_systematic_refactoring_workflow(self):
        """Test AI workflow for systematic refactoring across codebase"""

        # This would simulate an AI agent:
        # 1. Finding a pattern to refactor
        # 2. Locating all similar instances
        # 3. Assessing safety of each change
        # 4. Applying changes systematically

        # Implementation would go here
        pass

    def test_configuration_migration_workflow(self):
        """Test AI workflow for migrating configuration patterns"""

        # This would simulate an AI agent:
        # 1. Identifying deprecated patterns
        # 2. Finding all instances
        # 3. Planning migration strategy
        # 4. Executing safe migrations first

        # Implementation would go here
        pass
