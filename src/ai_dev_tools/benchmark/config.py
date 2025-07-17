"""
Configuration system for AI Development Tools benchmarking.

Provides structured configuration using pydantic models with validation,
environment-specific profiles, and runtime configuration management.
"""

from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Union

import tomllib
from pydantic import BaseModel, Field, field_validator, model_validator


class HardwareProfile(str, Enum):
    """Hardware profile types for benchmarking."""

    LIGHT = "light"  # Laptop/minimal (8GB+ RAM, 2+ cores)
    MEDIUM = "medium"  # Desktop/development (16GB+ RAM, 4+ cores)
    HEAVY = "heavy"  # Server/comprehensive (32GB+ RAM, 8+ cores)


class ExecutionMode(str, Enum):
    """Execution mode for benchmarks."""

    SEQUENTIAL = "sequential"  # Run tasks one after another
    PARALLEL = "parallel"  # Run tasks concurrently with limits
    ASYNC = "async"  # Full async execution


class OutputFormat(str, Enum):
    """Output format options."""

    JSON = "json"
    YAML = "yaml"
    MARKDOWN = "markdown"
    CSV = "csv"
    CONSOLE = "console"


class WorkflowType(str, Enum):
    """Types of workflows for benchmarking."""

    PATTERN_ANALYSIS = "pattern_analysis"
    SAFETY_CHECK = "safety_check"
    CONTEXT_ANALYSIS = "context_analysis"
    SYSTEMATIC_FIX = "systematic_fix"
    REPO_ANALYSIS = "repo_analysis"


class ModelInstance(BaseModel):
    """Configuration for a single model instance."""

    name: str = Field(..., description="Unique name for this model instance")
    model: str = Field(..., description="Model name/identifier")
    host: str = Field(default="localhost", description="Host address")
    port: int = Field(..., ge=1, le=65535, description="Port number")
    timeout: int = Field(default=30, ge=1, description="Request timeout in seconds")
    max_concurrent: int = Field(default=3, ge=1, description="Max concurrent requests")

    @property
    def url(self) -> str:
        """Get the full URL for this model instance."""
        return f"http://{self.host}:{self.port}"

    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError("Model instance name cannot be empty")
        return v.strip()


class BatchConfiguration(BaseModel):
    """Configuration for batch benchmark runs."""

    name: str = Field(..., description="Batch configuration name")
    profile: HardwareProfile = Field(..., description="Hardware profile to use")
    sample_size: int = Field(..., ge=1, le=100, description="Samples per task")
    repetitions: int = Field(default=1, ge=1, le=50, description="Number of repetitions")
    description: str = Field(default="", description="Human-readable description")
    timeout: int = Field(default=300, ge=30, description="Overall timeout in seconds")


class BenchmarkConfig(BaseModel):
    """Main configuration for benchmarking system."""

    # Hardware profiles
    profiles: Dict[HardwareProfile, List[ModelInstance]] = Field(
        default_factory=dict, description="Model instances by hardware profile"
    )

    # Sample sizes by profile
    sample_sizes: Dict[HardwareProfile, int] = Field(
        default={HardwareProfile.LIGHT: 3, HardwareProfile.MEDIUM: 6, HardwareProfile.HEAVY: 12},
        description="Default sample sizes by profile",
    )

    # Execution settings
    execution_mode: ExecutionMode = Field(default=ExecutionMode.ASYNC, description="Default execution mode")

    max_concurrent_batches: int = Field(default=2, ge=1, le=10, description="Maximum concurrent batch runs")

    # Output settings
    output_format: OutputFormat = Field(default=OutputFormat.JSON, description="Default output format")

    output_directory: Path = Field(default=Path("benchmark_results"), description="Directory for output files")

    # Docker settings
    docker_compose_file: Path = Field(default=Path("docker-compose.yml"), description="Path to docker-compose.yml")

    container_startup_timeout: int = Field(default=180, ge=30, description="Container startup timeout in seconds")

    # Batch configurations
    batch_configurations: Dict[str, BatchConfiguration] = Field(
        default_factory=dict, description="Predefined batch configurations"
    )

    # Task settings
    task_timeout: int = Field(default=30, ge=5, description="Individual task timeout in seconds")

    retry_attempts: int = Field(default=3, ge=1, le=10, description="Number of retry attempts for failed tasks")

    @model_validator(mode='after')
    def validate_profiles(self):
        """Ensure all profiles have valid configurations."""
        profiles = self.profiles
        sample_sizes = self.sample_sizes

        for profile in HardwareProfile:
            if profile not in profiles:
                raise ValueError(f"Missing configuration for profile: {profile}")

            if not profiles[profile]:
                raise ValueError(f"Empty model instances for profile: {profile}")

            if profile not in sample_sizes:
                raise ValueError(f"Missing sample size for profile: {profile}")

        return self

    @classmethod
    def from_toml(cls, toml_path: Union[str, Path]) -> "BenchmarkConfig":
        """Load configuration from TOML file."""
        toml_path = Path(toml_path)

        if not toml_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {toml_path}")

        with open(toml_path, "rb") as f:
            data = tomllib.load(f)

        # Extract benchmark configuration
        benchmark_config = data.get("tool", {}).get("ai-dev-tools", {}).get("benchmark", {})

        if not benchmark_config:
            # Return default config if no benchmark section found
            return cls._create_default_config()

        # Transform the TOML structure to match our model
        config_data = {"profiles": {}, "sample_sizes": {}, "batch_configurations": {}}

        # Process profiles
        ollama_profiles = benchmark_config.get("ollama_profiles", {})
        for profile_name, instances in ollama_profiles.items():
            try:
                profile = HardwareProfile(profile_name)
                config_data["profiles"][profile] = [ModelInstance(**instance) for instance in instances]
            except ValueError:
                continue  # Skip unknown profiles

        # Fill in missing profiles with defaults
        for profile in HardwareProfile:
            if profile not in config_data["profiles"]:
                config_data["profiles"][profile] = cls._get_default_profile_instances(profile)

        # Process sample sizes
        sample_sizes = benchmark_config.get("sample_sizes", {})
        for profile_name, size in sample_sizes.items():
            try:
                profile = HardwareProfile(profile_name)
                config_data["sample_sizes"][profile] = size
            except ValueError:
                continue  # Skip unknown profiles

        # Fill in missing sample sizes with defaults
        default_sample_sizes = {
            HardwareProfile.LIGHT: 3,
            HardwareProfile.MEDIUM: 6,
            HardwareProfile.HEAVY: 12
        }
        for profile in HardwareProfile:
            if profile not in config_data["sample_sizes"]:
                config_data["sample_sizes"][profile] = default_sample_sizes[profile]

        # Add predefined batch configurations
        config_data["batch_configurations"] = cls._create_default_batch_configs()

        # Add other settings from TOML or use defaults
        config_data.update(
            {
                "execution_mode": ExecutionMode(benchmark_config.get("execution_mode", "async")),
                "max_concurrent_batches": benchmark_config.get("max_concurrent_batches", 2),
                "output_format": OutputFormat(benchmark_config.get("output_format", "json")),
                "output_directory": Path(benchmark_config.get("output_directory", "benchmark_results")),
                "docker_compose_file": Path(benchmark_config.get("docker_compose_file", "docker-compose.yml")),
                "container_startup_timeout": benchmark_config.get("container_startup_timeout", 180),
                "task_timeout": benchmark_config.get("task_timeout", 30),
                "retry_attempts": benchmark_config.get("retry_attempts", 3),
            }
        )

        return cls(**config_data)

    @classmethod
    def _create_default_config(cls) -> "BenchmarkConfig":
        """Create a default configuration when no TOML file is found."""
        return cls(
            profiles={
                HardwareProfile.LIGHT: cls._get_default_profile_instances(HardwareProfile.LIGHT),
                HardwareProfile.MEDIUM: cls._get_default_profile_instances(HardwareProfile.MEDIUM),
                HardwareProfile.HEAVY: cls._get_default_profile_instances(HardwareProfile.HEAVY),
            },
            sample_sizes={
                HardwareProfile.LIGHT: 3,
                HardwareProfile.MEDIUM: 6,
                HardwareProfile.HEAVY: 12,
            },
            batch_configurations=cls._create_default_batch_configs(),
        )

    @staticmethod
    def _get_default_profile_instances(profile: HardwareProfile) -> List[ModelInstance]:
        """Get default model instances for a hardware profile."""
        if profile == HardwareProfile.LIGHT:
            return [
                ModelInstance(name="small", model="llama3.2:1b", port=11434)
            ]
        elif profile == HardwareProfile.MEDIUM:
            return [
                ModelInstance(name="small", model="llama3.2:1b", port=11434),
                ModelInstance(name="medium", model="llama3.2:3b", port=11435),
            ]
        else:  # HEAVY
            return [
                ModelInstance(name="small", model="llama3.2:1b", port=11434),
                ModelInstance(name="medium", model="llama3.2:3b", port=11435),
                ModelInstance(name="large", model="llama3.1:8b", port=11436),
                ModelInstance(name="code", model="codellama:7b", port=11437),
            ]

    @staticmethod
    def _create_default_batch_configs() -> Dict[str, BatchConfiguration]:
        """Create default batch configurations."""
        return {
            "quick": BatchConfiguration(
                name="quick",
                profile=HardwareProfile.LIGHT,
                sample_size=2,
                repetitions=1,
                description="Quick validation (2 samples)",
                timeout=300,
            ),
            "standard": BatchConfiguration(
                name="standard",
                profile=HardwareProfile.MEDIUM,
                sample_size=8,
                repetitions=1,
                description="Standard benchmarking (8 samples)",
                timeout=600,
            ),
            "comprehensive": BatchConfiguration(
                name="comprehensive",
                profile=HardwareProfile.HEAVY,
                sample_size=20,
                repetitions=1,
                description="Comprehensive analysis (20 samples)",
                timeout=1200,
            ),
            "scaling": BatchConfiguration(
                name="scaling",
                profile=HardwareProfile.MEDIUM,
                sample_size=5,
                repetitions=3,
                description="Model scaling test (5 samples × 3 runs)",
                timeout=900,
            ),
        }

    def get_profile_instances(self, profile: HardwareProfile) -> List[ModelInstance]:
        """Get model instances for a specific profile."""
        return self.profiles.get(profile, [])

    def get_sample_size(self, profile: HardwareProfile) -> int:
        """Get default sample size for a profile."""
        return self.sample_sizes.get(profile, 6)

    def get_batch_config(self, name: str) -> Optional[BatchConfiguration]:
        """Get batch configuration by name."""
        return self.batch_configurations.get(name)

    def validate_runtime(self) -> List[str]:
        """Validate runtime configuration and return any issues."""
        issues = []

        # Check if output directory is writable
        try:
            self.output_directory.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            issues.append(f"Cannot create output directory: {e}")

        # Check if docker-compose file exists
        if not self.docker_compose_file.exists():
            issues.append(f"Docker compose file not found: {self.docker_compose_file}")

        # Validate profile configurations
        for profile, instances in self.profiles.items():
            if not instances:
                issues.append(f"No model instances configured for profile: {profile}")

            # Check for port conflicts
            ports = [instance.port for instance in instances]
            if len(ports) != len(set(ports)):
                issues.append(f"Port conflicts in profile {profile}: {ports}")

        return issues


def load_config(config_path: Optional[Union[str, Path]] = None) -> BenchmarkConfig:
    """Load benchmark configuration from file or create default."""
    if config_path is None:
        # Try to find pyproject.toml in current directory or parent
        current_dir = Path.cwd()
        for path in [current_dir / "pyproject.toml", current_dir.parent / "pyproject.toml"]:
            if path.exists():
                config_path = path
                break

    if config_path and Path(config_path).exists():
        try:
            return BenchmarkConfig.from_toml(config_path)
        except Exception:
            # If loading fails, return default config
            return BenchmarkConfig._create_default_config()

    # Create default configuration
    return BenchmarkConfig._create_default_config()
