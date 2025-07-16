"""
Test configuration and fixtures for BDD tests
"""

import json
import tempfile
from pathlib import Path
from typing import Dict, Any

import pytest
from pytest_bdd import given, when, then, parsers

from ai_dev_tools.core.pattern_scanner import PatternScanner
from ai_dev_tools.core.safety_checker import SafetyChecker
from ai_dev_tools.core.repo_analyzer import RepoAnalyzer
from ai_dev_tools.agents.ai_agent import AIAgent


@pytest.fixture
def temp_repo():
    """Create a temporary repository for testing"""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_path = Path(temp_dir)
        yield repo_path


@pytest.fixture
def sample_files(temp_repo):
    """Create sample files with various patterns"""
    files = {}

    # Shell.nix with mkIf pattern
    shell_nix = temp_repo / "shell.nix"
    shell_nix.write_text("""
{ config, lib, pkgs, ... }:
{
  home.packages = lib.mkIf config.programs.development.enable [
    pkgs.git
    pkgs.vim
  ];
  
  programs.zsh.enable = true;
  
  home.file.".vimrc".text = "set number";
  
  environment.systemPackages = lib.mkIf config.services.docker.enable [
    pkgs.docker
    pkgs.docker-compose
  ];
}
""")
    files["shell.nix"] = shell_nix

    # Core.nix with similar pattern
    core_nix = temp_repo / "core.nix"
    core_nix.write_text("""
{ config, lib, pkgs, ... }:
{
  home.packages = lib.mkIf config.programs.core.enable [
    pkgs.curl
    pkgs.wget
  ];
  
  programs.bash.enable = true;
}
""")
    files["core.nix"] = core_nix

    # Development.nix with different pattern
    dev_nix = temp_repo / "development.nix"
    dev_nix.write_text("""
{ config, lib, pkgs, ... }:
{
  environment.systemPackages = lib.mkIf config.development.tools.enable [
    pkgs.nodejs
    pkgs.python3
  ];
}
""")
    files["development.nix"] = dev_nix

    # Unique file
    unique_nix = temp_repo / "unique.nix"
    unique_nix.write_text("""
{ config, lib, pkgs, ... }:
{
  services.nginx.enable = true;
  networking.firewall.allowedTCPPorts = [ 80 443 ];
}
""")
    files["unique.nix"] = unique_nix

    # Python source file
    utils_py = temp_repo / "src" / "utils.py"
    utils_py.parent.mkdir(exist_ok=True)
    utils_py.write_text("""
def helper_function():
    return "safe to modify"
""")
    files["src/utils.py"] = utils_py

    # Configuration file
    config_dir = temp_repo / "config"
    config_dir.mkdir(exist_ok=True)
    settings_json = config_dir / "settings.json"
    settings_json.write_text('{"debug": true}')
    files["config/settings.json"] = settings_json

    # System configuration
    config_nix = temp_repo / "configuration.nix"
    config_nix.write_text("""
{ config, pkgs, ... }:
{
  boot.loader.systemd-boot.enable = true;
  networking.hostName = "nixos";
}
""")
    files["configuration.nix"] = config_nix

    # Critical flake file
    flake_nix = temp_repo / "flake.nix"
    flake_nix.write_text("""
{
  description = "System flake";
  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
}
""")
    files["flake.nix"] = flake_nix

    return files


@pytest.fixture
def pattern_scanner():
    """Pattern scanner instance"""
    return PatternScanner()


@pytest.fixture
def safety_checker():
    """Safety checker instance"""
    return SafetyChecker()


@pytest.fixture
def repo_analyzer(temp_repo):
    """Repository analyzer instance"""
    return RepoAnalyzer(str(temp_repo))


@pytest.fixture
def ai_agent(temp_repo):
    """AI agent instance"""
    return AIAgent(str(temp_repo))


@pytest.fixture
def test_context():
    """Shared test context for storing results between steps"""
    return {}
