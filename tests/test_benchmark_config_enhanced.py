"""
Tests for the enhanced benchmark configuration system.

Tests the improved configuration loading, validation, and default handling.
"""

import pytest
import tempfile
import tomllib
from pathlib import Path
from unittest.mock import patch, Mock

from ai_dev_tools.benchmark.config import (
    BenchmarkConfig,
    HardwareProfile,
    ModelInstance,
    BatchConfiguration,
    ExecutionMode,
    OutputFormat,
    load_config
)


class TestEnhancedBenchmarkConfig:
    """Test the enhanced benchmark configuration system."""
    
    def test_create_default_config(self):
        """Test creating default configuration."""
        config = BenchmarkConfig._create_default_config()
        
        assert isinstance(config, BenchmarkConfig)
        assert len(config.profiles) == 3
        assert HardwareProfile.LIGHT in config.profiles
        assert HardwareProfile.MEDIUM in config.profiles
        assert HardwareProfile.HEAVY in config.profiles
        
        # Check sample sizes
        assert config.sample_sizes[HardwareProfile.LIGHT] == 3
        assert config.sample_sizes[HardwareProfile.MEDIUM] == 6
        assert config.sample_sizes[HardwareProfile.HEAVY] == 12
        
        # Check batch configurations
        assert "quick" in config.batch_configurations
        assert "standard" in config.batch_configurations
        assert "comprehensive" in config.batch_configurations
        assert "scaling" in config.batch_configurations
    
    def test_get_default_profile_instances(self):
        """Test getting default profile instances."""
        # Test light profile
        light_instances = BenchmarkConfig._get_default_profile_instances(HardwareProfile.LIGHT)
        assert len(light_instances) == 1
        assert light_instances[0].name == "small"
        assert light_instances[0].model == "llama3.2:1b"
        assert light_instances[0].port == 11434
        
        # Test medium profile
        medium_instances = BenchmarkConfig._get_default_profile_instances(HardwareProfile.MEDIUM)
        assert len(medium_instances) == 2
        assert medium_instances[0].name == "small"
        assert medium_instances[1].name == "medium"
        assert medium_instances[0].model == "llama3.2:1b"
        assert medium_instances[1].model == "llama3.2:3b"
        
        # Test heavy profile
        heavy_instances = BenchmarkConfig._get_default_profile_instances(HardwareProfile.HEAVY)
        assert len(heavy_instances) == 4
        assert heavy_instances[0].name == "small"
        assert heavy_instances[1].name == "medium"
        assert heavy_instances[2].name == "large"
        assert heavy_instances[3].name == "code"
        assert heavy_instances[0].model == "llama3.2:1b"
        assert heavy_instances[1].model == "llama3.2:3b"
        assert heavy_instances[2].model == "llama3.1:8b"
        assert heavy_instances[3].model == "codellama:7b"
    
    def test_from_toml_with_no_benchmark_section(self):
        """Test loading from TOML file with no benchmark section."""
        toml_content = """
        [tool.other-tool]
        setting = "value"
        """
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
            f.write(toml_content)
            f.flush()
            
            config = BenchmarkConfig.from_toml(f.name)
            
            # Should return default config
            assert len(config.profiles) == 3
            assert config.sample_sizes[HardwareProfile.LIGHT] == 3
            assert config.execution_mode == ExecutionMode.ASYNC
            assert config.output_format == OutputFormat.JSON
            
            Path(f.name).unlink()  # Clean up
    
    def test_from_toml_with_partial_configuration(self):
        """Test loading from TOML file with partial configuration."""
        toml_content = """
        [tool.ai-dev-tools.benchmark]
        execution_mode = "sequential"
        output_format = "markdown"
        
        [tool.ai-dev-tools.benchmark.sample_sizes]
        light = 2
        medium = 4
        
        [[tool.ai-dev-tools.benchmark.ollama_profiles.light]]
        name = "custom-small"
        model = "custom:1b"
        port = 11444
        """
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
            f.write(toml_content)
            f.flush()
            
            config = BenchmarkConfig.from_toml(f.name)
            
            # Should use custom settings where provided
            assert config.execution_mode == ExecutionMode.SEQUENTIAL
            assert config.output_format == OutputFormat.MARKDOWN
            assert config.sample_sizes[HardwareProfile.LIGHT] == 2
            assert config.sample_sizes[HardwareProfile.MEDIUM] == 4
            assert config.sample_sizes[HardwareProfile.HEAVY] == 12  # Default
            
            # Should use custom profile where provided
            light_instances = config.profiles[HardwareProfile.LIGHT]
            assert len(light_instances) == 1
            assert light_instances[0].name == "custom-small"
            assert light_instances[0].model == "custom:1b"
            assert light_instances[0].port == 11444
            
            # Should use defaults for missing profiles
            medium_instances = config.profiles[HardwareProfile.MEDIUM]
            assert len(medium_instances) == 2  # Default medium profile
            
            Path(f.name).unlink()  # Clean up
    
    def test_from_toml_with_complete_configuration(self):
        """Test loading from TOML file with complete configuration."""
        toml_content = """
        [tool.ai-dev-tools.benchmark]
        execution_mode = "parallel"
        output_format = "csv"
        output_directory = "/custom/output"
        docker_compose_file = "/custom/docker-compose.yml"
        container_startup_timeout = 300
        task_timeout = 60
        retry_attempts = 5
        max_concurrent_batches = 4
        
        [tool.ai-dev-tools.benchmark.sample_sizes]
        light = 1
        medium = 3
        heavy = 6
        
        [[tool.ai-dev-tools.benchmark.ollama_profiles.light]]
        name = "tiny"
        model = "llama3.2:1b"
        port = 11434
        timeout = 20
        max_concurrent = 2
        
        [[tool.ai-dev-tools.benchmark.ollama_profiles.medium]]
        name = "small"
        model = "llama3.2:1b"
        port = 11434
        
        [[tool.ai-dev-tools.benchmark.ollama_profiles.medium]]
        name = "medium"
        model = "llama3.2:3b"
        port = 11435
        
        [[tool.ai-dev-tools.benchmark.ollama_profiles.heavy]]
        name = "small"
        model = "llama3.2:1b"
        port = 11434
        
        [[tool.ai-dev-tools.benchmark.ollama_profiles.heavy]]
        name = "large"
        model = "llama3.1:8b"
        port = 11436
        """
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
            f.write(toml_content)
            f.flush()
            
            config = BenchmarkConfig.from_toml(f.name)
            
            # Check all custom settings
            assert config.execution_mode == ExecutionMode.PARALLEL
            assert config.output_format == OutputFormat.CSV
            assert str(config.output_directory) == "/custom/output"
            assert str(config.docker_compose_file) == "/custom/docker-compose.yml"
            assert config.container_startup_timeout == 300
            assert config.task_timeout == 60
            assert config.retry_attempts == 5
            assert config.max_concurrent_batches == 4
            
            # Check custom sample sizes
            assert config.sample_sizes[HardwareProfile.LIGHT] == 1
            assert config.sample_sizes[HardwareProfile.MEDIUM] == 3
            assert config.sample_sizes[HardwareProfile.HEAVY] == 6
            
            # Check custom profiles
            light_instances = config.profiles[HardwareProfile.LIGHT]
            assert len(light_instances) == 1
            assert light_instances[0].name == "tiny"
            assert light_instances[0].timeout == 20
            assert light_instances[0].max_concurrent == 2
            
            medium_instances = config.profiles[HardwareProfile.MEDIUM]
            assert len(medium_instances) == 2
            
            heavy_instances = config.profiles[HardwareProfile.HEAVY]
            assert len(heavy_instances) == 2  # Only 2 specified in TOML
            
            Path(f.name).unlink()  # Clean up
    
    def test_from_toml_file_not_found(self):
        """Test loading from non-existent TOML file."""
        with pytest.raises(FileNotFoundError):
            BenchmarkConfig.from_toml("/non/existent/file.toml")
    
    def test_from_toml_invalid_profile_skipped(self):
        """Test that invalid profiles are skipped during loading."""
        toml_content = """
        [tool.ai-dev-tools.benchmark]
        
        [[tool.ai-dev-tools.benchmark.ollama_profiles.invalid_profile]]
        name = "test"
        model = "test:1b"
        port = 11434
        
        [[tool.ai-dev-tools.benchmark.ollama_profiles.light]]
        name = "valid"
        model = "llama3.2:1b"
        port = 11434
        
        [tool.ai-dev-tools.benchmark.sample_sizes]
        invalid_profile = 5
        light = 2
        """
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
            f.write(toml_content)
            f.flush()
            
            config = BenchmarkConfig.from_toml(f.name)
            
            # Should have valid profile
            assert HardwareProfile.LIGHT in config.profiles
            assert len(config.profiles[HardwareProfile.LIGHT]) == 1
            assert config.profiles[HardwareProfile.LIGHT][0].name == "valid"
            
            # Should have default profiles for medium and heavy
            assert len(config.profiles[HardwareProfile.MEDIUM]) == 2
            assert len(config.profiles[HardwareProfile.HEAVY]) == 4
            
            # Should have valid sample size
            assert config.sample_sizes[HardwareProfile.LIGHT] == 2
            
            Path(f.name).unlink()  # Clean up
    
    def test_create_default_batch_configs(self):
        """Test creation of default batch configurations."""
        batch_configs = BenchmarkConfig._create_default_batch_configs()
        
        assert len(batch_configs) == 4
        assert "quick" in batch_configs
        assert "standard" in batch_configs
        assert "comprehensive" in batch_configs
        assert "scaling" in batch_configs
        
        # Check quick config
        quick_config = batch_configs["quick"]
        assert quick_config.name == "quick"
        assert quick_config.profile == HardwareProfile.LIGHT
        assert quick_config.sample_size == 2
        assert quick_config.repetitions == 1
        assert quick_config.timeout == 300
        
        # Check standard config
        standard_config = batch_configs["standard"]
        assert standard_config.name == "standard"
        assert standard_config.profile == HardwareProfile.MEDIUM
        assert standard_config.sample_size == 8
        
        # Check comprehensive config
        comprehensive_config = batch_configs["comprehensive"]
        assert comprehensive_config.name == "comprehensive"
        assert comprehensive_config.profile == HardwareProfile.HEAVY
        assert comprehensive_config.sample_size == 20
        
        # Check scaling config
        scaling_config = batch_configs["scaling"]
        assert scaling_config.name == "scaling"
        assert scaling_config.profile == HardwareProfile.MEDIUM
        assert scaling_config.sample_size == 5
        assert scaling_config.repetitions == 3
    
    def test_get_profile_instances(self):
        """Test getting profile instances."""
        config = BenchmarkConfig._create_default_config()
        
        light_instances = config.get_profile_instances(HardwareProfile.LIGHT)
        assert len(light_instances) == 1
        assert light_instances[0].name == "small"
        
        medium_instances = config.get_profile_instances(HardwareProfile.MEDIUM)
        assert len(medium_instances) == 2
        
        heavy_instances = config.get_profile_instances(HardwareProfile.HEAVY)
        assert len(heavy_instances) == 4
        
        # Test non-existent profile
        empty_instances = config.get_profile_instances("non_existent")
        assert empty_instances == []
    
    def test_get_sample_size(self):
        """Test getting sample size for profiles."""
        config = BenchmarkConfig._create_default_config()
        
        assert config.get_sample_size(HardwareProfile.LIGHT) == 3
        assert config.get_sample_size(HardwareProfile.MEDIUM) == 6
        assert config.get_sample_size(HardwareProfile.HEAVY) == 12
        
        # Test non-existent profile
        assert config.get_sample_size("non_existent") == 6  # Default
    
    def test_get_batch_config(self):
        """Test getting batch configuration."""
        config = BenchmarkConfig._create_default_config()
        
        quick_config = config.get_batch_config("quick")
        assert quick_config is not None
        assert quick_config.name == "quick"
        
        standard_config = config.get_batch_config("standard")
        assert standard_config is not None
        assert standard_config.name == "standard"
        
        # Test non-existent batch
        non_existent = config.get_batch_config("non_existent")
        assert non_existent is None
    
    def test_validate_runtime(self):
        """Test runtime validation."""
        config = BenchmarkConfig._create_default_config()
        
        # Test with valid configuration - may or may not have issues depending on environment
        issues = config.validate_runtime()
        
        # Test with missing docker-compose file
        config.docker_compose_file = Path("/nonexistent/docker-compose.yml")
        issues = config.validate_runtime()
        assert len(issues) > 0
        assert any("Docker compose file not found" in issue for issue in issues)
        
        # Test with empty profiles
        config.profiles[HardwareProfile.LIGHT] = []
        issues = config.validate_runtime()
        assert any("No model instances configured for profile: light" in issue for issue in issues)
        
        # Test with port conflicts
        config.profiles[HardwareProfile.LIGHT] = [
            ModelInstance(name="test1", model="test:1b", port=11434),
            ModelInstance(name="test2", model="test:2b", port=11434)  # Same port
        ]
        issues = config.validate_runtime()
        assert any("Port conflicts" in issue for issue in issues)


class TestLoadConfig:
    """Test the enhanced load_config function."""
    
    def test_load_config_with_valid_path(self):
        """Test loading config with valid path."""
        toml_content = """
        [tool.ai-dev-tools.benchmark]
        execution_mode = "sequential"
        
        [tool.ai-dev-tools.benchmark.sample_sizes]
        light = 2
        """
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
            f.write(toml_content)
            f.flush()
            
            config = load_config(f.name)
            
            assert config.execution_mode == ExecutionMode.SEQUENTIAL
            assert config.sample_sizes[HardwareProfile.LIGHT] == 2
            
            Path(f.name).unlink()  # Clean up
    
    def test_load_config_with_invalid_path(self):
        """Test loading config with invalid path."""
        config = load_config("/non/existent/path.toml")
        
        # Should return default config
        assert len(config.profiles) == 3
        assert config.execution_mode == ExecutionMode.ASYNC
        assert config.output_format == OutputFormat.JSON
    
    def test_load_config_with_corrupted_file(self):
        """Test loading config with corrupted TOML file."""
        corrupted_content = """
        [tool.ai-dev-tools.benchmark
        invalid toml content
        """
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
            f.write(corrupted_content)
            f.flush()
            
            config = load_config(f.name)
            
            # Should return default config on parsing error
            assert len(config.profiles) == 3
            assert config.execution_mode == ExecutionMode.ASYNC
            
            Path(f.name).unlink()  # Clean up
    
    def test_load_config_auto_discovery(self):
        """Test automatic discovery of pyproject.toml."""
        toml_content = """
        [tool.ai-dev-tools.benchmark]
        execution_mode = "parallel"
        """
        
        with tempfile.TemporaryDirectory() as temp_dir:
            toml_path = Path(temp_dir) / "pyproject.toml"
            toml_path.write_text(toml_content)
            
            # Change to temp directory
            original_cwd = Path.cwd()
            try:
                import os
                os.chdir(temp_dir)
                
                config = load_config()
                
                assert config.execution_mode == ExecutionMode.PARALLEL
                
            finally:
                os.chdir(original_cwd)
    
    def test_load_config_parent_directory_discovery(self):
        """Test discovery of pyproject.toml in parent directory."""
        toml_content = """
        [tool.ai-dev-tools.benchmark]
        task_timeout = 45
        """
        
        with tempfile.TemporaryDirectory() as temp_dir:
            parent_dir = Path(temp_dir)
            child_dir = parent_dir / "child"
            child_dir.mkdir()
            
            toml_path = parent_dir / "pyproject.toml"
            toml_path.write_text(toml_content)
            
            # Change to child directory
            original_cwd = Path.cwd()
            try:
                import os
                os.chdir(child_dir)
                
                config = load_config()
                
                assert config.task_timeout == 45
                
            finally:
                os.chdir(original_cwd)
    
    def test_load_config_no_discovery(self):
        """Test load_config when no pyproject.toml is found."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Change to temp directory with no pyproject.toml
            original_cwd = Path.cwd()
            try:
                import os
                os.chdir(temp_dir)
                
                config = load_config()
                
                # Should return default config
                assert len(config.profiles) == 3
                assert config.execution_mode == ExecutionMode.ASYNC
                
            finally:
                os.chdir(original_cwd)


class TestModelInstance:
    """Test ModelInstance enhancements."""
    
    def test_model_instance_url_property(self):
        """Test the URL property of ModelInstance."""
        instance = ModelInstance(
            name="test",
            model="test:1b",
            host="custom.host",
            port=8080
        )
        
        assert instance.url == "http://custom.host:8080"
    
    def test_model_instance_name_validation(self):
        """Test name validation for ModelInstance."""
        # Valid name
        instance = ModelInstance(
            name="valid-name",
            model="test:1b",
            port=11434
        )
        assert instance.name == "valid-name"
        
        # Empty name should raise validation error
        with pytest.raises(ValueError, match="Model instance name cannot be empty"):
            ModelInstance(
                name="",
                model="test:1b",
                port=11434
            )
        
        # Whitespace-only name should raise validation error  
        with pytest.raises(ValueError, match="Model instance name cannot be empty"):
            ModelInstance(
                name="   ",
                model="test:1b",
                port=11434
            )
        
        # Name with whitespace should be stripped
        instance = ModelInstance(
            name="  spaced-name  ",
            model="test:1b",
            port=11434
        )
        assert instance.name == "spaced-name"


class TestBatchConfiguration:
    """Test BatchConfiguration enhancements."""
    
    def test_batch_configuration_creation(self):
        """Test creating batch configuration."""
        batch_config = BatchConfiguration(
            name="test_batch",
            profile=HardwareProfile.MEDIUM,
            sample_size=10,
            repetitions=2,
            description="Test batch configuration",
            timeout=600
        )
        
        assert batch_config.name == "test_batch"
        assert batch_config.profile == HardwareProfile.MEDIUM
        assert batch_config.sample_size == 10
        assert batch_config.repetitions == 2
        assert batch_config.description == "Test batch configuration"
        assert batch_config.timeout == 600
    
    def test_batch_configuration_validation(self):
        """Test batch configuration validation."""
        # Valid configuration
        batch_config = BatchConfiguration(
            name="valid",
            profile=HardwareProfile.LIGHT,
            sample_size=5,
            repetitions=1,
            timeout=300
        )
        assert batch_config.sample_size == 5
        
        # Invalid sample size (too low)
        with pytest.raises(ValueError):
            BatchConfiguration(
                name="invalid",
                profile=HardwareProfile.LIGHT,
                sample_size=0,
                repetitions=1,
                timeout=300
            )
        
        # Invalid sample size (too high)
        with pytest.raises(ValueError):
            BatchConfiguration(
                name="invalid",
                profile=HardwareProfile.LIGHT,
                sample_size=101,
                repetitions=1,
                timeout=300
            )
        
        # Invalid repetitions (too low)
        with pytest.raises(ValueError):
            BatchConfiguration(
                name="invalid",
                profile=HardwareProfile.LIGHT,
                sample_size=5,
                repetitions=0,
                timeout=300
            )
        
        # Invalid timeout (too low)
        with pytest.raises(ValueError):
            BatchConfiguration(
                name="invalid",
                profile=HardwareProfile.LIGHT,
                sample_size=5,
                repetitions=1,
                timeout=29
            )