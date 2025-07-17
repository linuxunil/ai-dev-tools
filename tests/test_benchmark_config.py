"""
Tests for benchmark configuration system.
"""

import pytest
from pathlib import Path
from typing import Dict, Any
import tempfile
import tomllib

from ai_dev_tools.benchmark.config import (
    BenchmarkConfig,
    HardwareProfile,
    ModelInstance,
    BatchConfiguration,
    ExecutionMode,
    OutputFormat,
    WorkflowType,
    load_config
)


class TestModelInstance:
    """Test ModelInstance configuration."""
    
    def test_model_instance_creation(self):
        """Test basic model instance creation."""
        instance = ModelInstance(
            name="test_model",
            model="llama3.2:1b",
            port=11434
        )
        
        assert instance.name == "test_model"
        assert instance.model == "llama3.2:1b"
        assert instance.host == "localhost"
        assert instance.port == 11434
        assert instance.url == "http://localhost:11434"
        assert instance.timeout == 30
        assert instance.max_concurrent == 3
    
    def test_model_instance_custom_host(self):
        """Test model instance with custom host."""
        instance = ModelInstance(
            name="remote_model",
            model="llama3.2:3b",
            host="192.168.1.100",
            port=11435
        )
        
        assert instance.host == "192.168.1.100"
        assert instance.url == "http://192.168.1.100:11435"
    
    def test_model_instance_validation(self):
        """Test model instance validation."""
        with pytest.raises(ValueError):
            ModelInstance(name="", model="llama3.2:1b", port=11434)
        
        with pytest.raises(ValueError):
            ModelInstance(name="test", model="llama3.2:1b", port=0)
        
        with pytest.raises(ValueError):
            ModelInstance(name="test", model="llama3.2:1b", port=70000)


class TestBatchConfiguration:
    """Test BatchConfiguration."""
    
    def test_batch_configuration_creation(self):
        """Test basic batch configuration creation."""
        config = BatchConfiguration(
            name="test_batch",
            profile=HardwareProfile.MEDIUM,
            sample_size=10,
            description="Test batch configuration"
        )
        
        assert config.name == "test_batch"
        assert config.profile == HardwareProfile.MEDIUM
        assert config.sample_size == 10
        assert config.repetitions == 1
        assert config.description == "Test batch configuration"
        assert config.timeout == 300
    
    def test_batch_configuration_validation(self):
        """Test batch configuration validation."""
        with pytest.raises(ValueError):
            BatchConfiguration(
                name="test",
                profile=HardwareProfile.MEDIUM,
                sample_size=0  # Invalid
            )
        
        with pytest.raises(ValueError):
            BatchConfiguration(
                name="test",
                profile=HardwareProfile.MEDIUM,
                sample_size=101  # Too large
            )


class TestBenchmarkConfig:
    """Test BenchmarkConfig."""
    
    def test_default_config_creation(self):
        """Test creating default configuration."""
        config = BenchmarkConfig()
        
        assert len(config.profiles) == 0  # No profiles by default
        assert config.execution_mode == ExecutionMode.ASYNC
        assert config.output_format == OutputFormat.JSON
        assert config.output_directory == Path("benchmark_results")
        assert config.max_concurrent_batches == 2
        assert config.container_startup_timeout == 180
        assert config.task_timeout == 30
        assert config.retry_attempts == 3
    
    def test_config_with_profiles(self):
        """Test configuration with profiles."""
        light_instance = ModelInstance(name="small", model="llama3.2:1b", port=11434)
        medium_instances = [
            ModelInstance(name="small", model="llama3.2:1b", port=11434),
            ModelInstance(name="medium", model="llama3.2:3b", port=11435)
        ]
        
        config = BenchmarkConfig(
            profiles={
                HardwareProfile.LIGHT: [light_instance],
                HardwareProfile.MEDIUM: medium_instances,
                HardwareProfile.HEAVY: medium_instances  # Same as medium for test
            }
        )
        
        assert len(config.profiles) == 3
        assert len(config.get_profile_instances(HardwareProfile.LIGHT)) == 1
        assert len(config.get_profile_instances(HardwareProfile.MEDIUM)) == 2
        assert config.get_sample_size(HardwareProfile.LIGHT) == 3
        assert config.get_sample_size(HardwareProfile.MEDIUM) == 6
    
    def test_config_validation(self):
        """Test configuration validation."""
        # Missing profile should raise error
        with pytest.raises(ValueError):
            BenchmarkConfig(
                profiles={
                    HardwareProfile.LIGHT: [ModelInstance(name="test", model="llama3.2:1b", port=11434)]
                    # Missing MEDIUM and HEAVY profiles
                }
            )
        
        # Empty profile should raise error
        with pytest.raises(ValueError):
            BenchmarkConfig(
                profiles={
                    HardwareProfile.LIGHT: [],  # Empty
                    HardwareProfile.MEDIUM: [ModelInstance(name="test", model="llama3.2:1b", port=11434)],
                    HardwareProfile.HEAVY: [ModelInstance(name="test", model="llama3.2:1b", port=11434)]
                }
            )
    
    def test_batch_configurations(self):
        """Test batch configurations."""
        config = BenchmarkConfig(
            profiles={
                HardwareProfile.LIGHT: [ModelInstance(name="test", model="llama3.2:1b", port=11434)],
                HardwareProfile.MEDIUM: [ModelInstance(name="test", model="llama3.2:1b", port=11434)],
                HardwareProfile.HEAVY: [ModelInstance(name="test", model="llama3.2:1b", port=11434)]
            }
        )
        
        # Should have default batch configurations
        assert len(config.batch_configurations) > 0
        assert "quick" in config.batch_configurations
        assert "standard" in config.batch_configurations
        assert "comprehensive" in config.batch_configurations
        
        # Test getting batch config
        quick_config = config.get_batch_config("quick")
        assert quick_config is not None
        assert quick_config.profile == HardwareProfile.LIGHT
        assert quick_config.sample_size == 2
    
    def test_runtime_validation(self):
        """Test runtime validation."""
        config = BenchmarkConfig(
            profiles={
                HardwareProfile.LIGHT: [ModelInstance(name="test", model="llama3.2:1b", port=11434)],
                HardwareProfile.MEDIUM: [ModelInstance(name="test", model="llama3.2:1b", port=11434)],
                HardwareProfile.HEAVY: [ModelInstance(name="test", model="llama3.2:1b", port=11434)]
            },
            docker_compose_file=Path("nonexistent.yml")
        )
        
        issues = config.validate_runtime()
        assert len(issues) > 0
        assert any("Docker compose file not found" in issue for issue in issues)


class TestConfigLoading:
    """Test configuration loading from TOML files."""
    
    def test_load_config_from_toml(self):
        """Test loading configuration from TOML file."""
        toml_content = """
[tool.ai-dev-tools.benchmark]
execution_mode = "parallel"
output_format = "markdown"
task_timeout = 45

[tool.ai-dev-tools.benchmark.ollama_profiles]
light = [
    { name = "small", model = "llama3.2:1b", host = "localhost", port = 11434 }
]
medium = [
    { name = "small", model = "llama3.2:1b", host = "localhost", port = 11434 },
    { name = "medium", model = "llama3.2:3b", host = "localhost", port = 11435 }
]
heavy = [
    { name = "small", model = "llama3.2:1b", host = "localhost", port = 11434 },
    { name = "medium", model = "llama3.2:3b", host = "localhost", port = 11435 },
    { name = "large", model = "llama3.1:8b", host = "localhost", port = 11436 }
]

[tool.ai-dev-tools.benchmark.sample_sizes]
light = 3
medium = 6
heavy = 12
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
            f.write(toml_content)
            f.flush()
            
            config = BenchmarkConfig.from_toml(f.name)
            
            assert config.execution_mode == ExecutionMode.PARALLEL
            assert config.output_format == OutputFormat.MARKDOWN
            assert config.task_timeout == 45
            
            assert len(config.profiles) == 3
            assert len(config.get_profile_instances(HardwareProfile.LIGHT)) == 1
            assert len(config.get_profile_instances(HardwareProfile.MEDIUM)) == 2
            assert len(config.get_profile_instances(HardwareProfile.HEAVY)) == 3
            
            assert config.get_sample_size(HardwareProfile.LIGHT) == 3
            assert config.get_sample_size(HardwareProfile.MEDIUM) == 6
            assert config.get_sample_size(HardwareProfile.HEAVY) == 12
    
    def test_load_config_file_not_found(self):
        """Test loading config when file doesn't exist."""
        with pytest.raises(FileNotFoundError):
            BenchmarkConfig.from_toml("nonexistent.toml")
    
    def test_load_config_no_benchmark_section(self):
        """Test loading config with no benchmark section."""
        toml_content = """
[tool.other]
setting = "value"
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
            f.write(toml_content)
            f.flush()
            
            # Should return default config, not raise error
            config = BenchmarkConfig.from_toml(f.name)
            assert len(config.profiles) == 3
            assert config.execution_mode == ExecutionMode.ASYNC
    
    def test_load_config_default(self):
        """Test loading default configuration."""
        config = load_config()
        
        # Should return a valid configuration
        assert isinstance(config, BenchmarkConfig)
        assert len(config.profiles) > 0
        assert len(config.batch_configurations) > 0


class TestEnums:
    """Test enum classes."""
    
    def test_hardware_profile_enum(self):
        """Test HardwareProfile enum."""
        assert HardwareProfile.LIGHT.value == "light"
        assert HardwareProfile.MEDIUM.value == "medium"
        assert HardwareProfile.HEAVY.value == "heavy"
    
    def test_execution_mode_enum(self):
        """Test ExecutionMode enum."""
        assert ExecutionMode.SEQUENTIAL.value == "sequential"
        assert ExecutionMode.PARALLEL.value == "parallel"
        assert ExecutionMode.ASYNC.value == "async"
    
    def test_output_format_enum(self):
        """Test OutputFormat enum."""
        assert OutputFormat.JSON.value == "json"
        assert OutputFormat.YAML.value == "yaml"
        assert OutputFormat.MARKDOWN.value == "markdown"
        assert OutputFormat.CSV.value == "csv"
        assert OutputFormat.CONSOLE.value == "console"
    
    def test_workflow_type_enum(self):
        """Test WorkflowType enum."""
        assert WorkflowType.PATTERN_ANALYSIS.value == "pattern_analysis"
        assert WorkflowType.SAFETY_CHECK.value == "safety_check"
        assert WorkflowType.CONTEXT_ANALYSIS.value == "context_analysis"
        assert WorkflowType.SYSTEMATIC_FIX.value == "systematic_fix"
        assert WorkflowType.REPO_ANALYSIS.value == "repo_analysis"


if __name__ == "__main__":
    pytest.main([__file__])