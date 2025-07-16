{
  description = "AI Development Tools - Exit-code-first tools for AI workflows";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        
        pythonEnv = pkgs.python3.withPackages (ps: with ps; [
          # Core dependencies
          setuptools
          wheel
          pip
          
          # Development dependencies
          pytest
          pytest-cov
          pytest-bdd
          ruff
          mypy
          
          # Runtime dependencies
          click
        ]);
      in
      {
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            # Python environment
            pythonEnv
            uv  # Fast Python package manager
            
            # AI/ML tools
            ollama  # Local LLM runtime
            
            # Development tools
            git
            curl
            jq
            zsh  # Shell
            
            # Build tools
            gnumake
            
            # Documentation
            mdbook
          ];

          shellHook = ''
            echo "🚀 AI Development Tools Development Environment"
            echo "================================================"
            echo "Python: $(python --version)"
            echo "Ollama: $(ollama --version 2>/dev/null || echo 'Available but not running')"
            echo "UV: $(uv --version)"
            echo ""
            echo "💡 Quick start:"
            echo "  • Start Ollama: ollama serve"
            echo "  • Install deps: uv pip install -e ."
            echo "  • Run tests: pytest"
            echo "  • Safety check: python standalone_safety_check.py <file>"
            echo "  • Pattern scan: python standalone_pattern_scanner.py <file> <line>"
            echo ""
            
            # Set up Python path
            export PYTHONPATH="$PWD/src:$PYTHONPATH"
            
            # Use zsh as the shell
            export SHELL=${pkgs.zsh}/bin/zsh
            
            # Create .env file if it doesn't exist
            if [ ! -f .env ]; then
              echo "OLLAMA_HOST=127.0.0.1:11434" > .env
              echo "Created .env file with Ollama configuration"
            fi
            
            # Start zsh if not already in it
            if [ "$0" != "${pkgs.zsh}/bin/zsh" ]; then
              exec ${pkgs.zsh}/bin/zsh
            fi
          '';
        };

        packages.default = pkgs.python3Packages.buildPythonPackage {
          pname = "ai-dev-tools";
          version = "0.1.0";
          src = ./.;
          
          propagatedBuildInputs = with pkgs.python3Packages; [
            click
          ];
          
          meta = with pkgs.lib; {
            description = "Exit-code-first AI development tools";
            homepage = "https://github.com/user/ai-dev-tools";
            license = licenses.mit;
          };
        };
      }
    );
}
