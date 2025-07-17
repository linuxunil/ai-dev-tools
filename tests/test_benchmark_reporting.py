"""
Tests for the enhanced benchmark reporting system.

Tests the new visualization and reporting features.
"""

import pytest
from unittest.mock import Mock, patch, mock_open
from pathlib import Path
import json

from ai_dev_tools.benchmark.reporting import ReportGenerator
from ai_dev_tools.benchmark.config import OutputFormat


class TestReportGenerator:
    """Test the enhanced report generator."""
    
    @pytest.fixture
    def sample_benchmark_data(self):
        """Create sample benchmark data for testing."""
        return {
            "benchmark_info": {
                "profile": "medium",
                "total_tasks": 3,
                "sample_size": 5,
                "execution_mode": "async",
                "timestamp": 1234567890.0
            },
            "overall_metrics": {
                "total_tasks": 3,
                "completed_tasks": 3,
                "failed_tasks": 0,
                "success_rate": 1.0,
                "average_task_duration": 2.5,
                "total_tokens": 1500,
                "tokens_per_second": 600.0,
                "throughput": 1.2,
                "efficiency_score": 0.85,
                "error_types": {"timeout": 1, "connection": 2}
            },
            "comparison_metrics": {
                "token_reduction_percent": 25.0,
                "time_reduction_percent": 30.0,
                "efficiency_improvement_percent": 15.0,
                "sample_size": 5,
                "baseline_metrics": {
                    "average_task_duration": 3.5,
                    "total_tokens": 2000,
                    "success_rate": 0.9,
                    "throughput": 0.8,
                    "efficiency_score": 0.7
                },
                "tools_metrics": {
                    "average_task_duration": 2.5,
                    "total_tokens": 1500,
                    "success_rate": 1.0,
                    "throughput": 1.2,
                    "efficiency_score": 0.85
                }
            },
            "metrics_by_task": {
                "task1": {
                    "success_rate": 1.0,
                    "average_task_duration": 2.0,
                    "total_tokens": 500,
                    "efficiency_score": 0.9
                },
                "task2": {
                    "success_rate": 0.8,
                    "average_task_duration": 3.0,
                    "total_tokens": 600,
                    "efficiency_score": 0.75
                }
            },
            "metrics_by_model": {
                "small": {
                    "success_rate": 0.95,
                    "average_task_duration": 2.2,
                    "total_tokens": 700,
                    "efficiency_score": 0.88
                },
                "medium": {
                    "success_rate": 1.0,
                    "average_task_duration": 2.8,
                    "total_tokens": 800,
                    "efficiency_score": 0.82
                }
            }
        }
    
    @pytest.fixture
    def report_generator(self):
        """Create a report generator instance."""
        return ReportGenerator("/tmp/test_output")
    
    def test_generate_json_report(self, report_generator, sample_benchmark_data):
        """Test generating JSON format report."""
        with patch("builtins.open", mock_open()) as mock_file:
            result_path = report_generator.generate_report(
                sample_benchmark_data,
                OutputFormat.JSON,
                "test_report"
            )
            
            assert result_path.endswith("test_report.json")
            mock_file.assert_called_once()
            
            # Check that JSON content was written
            handle = mock_file()
            written_content = "".join(call.args[0] for call in handle.write.call_args_list)
            parsed_content = json.loads(written_content)
            
            assert parsed_content["benchmark_info"]["profile"] == "medium"
            assert parsed_content["overall_metrics"]["success_rate"] == 1.0
    
    def test_generate_markdown_report(self, report_generator, sample_benchmark_data):
        """Test generating Markdown format report."""
        with patch("builtins.open", mock_open()) as mock_file:
            result_path = report_generator.generate_report(
                sample_benchmark_data,
                OutputFormat.MARKDOWN,
                "test_report"
            )
            
            assert result_path.endswith("test_report.markdown")
            mock_file.assert_called_once()
            
            # Check that markdown content was written
            handle = mock_file()
            written_content = "".join(call.args[0] for call in handle.write.call_args_list)
            
            assert "# AI Development Tools Benchmark Report" in written_content
            assert "**Profile:** MEDIUM" in written_content
            assert "## Overall Performance" in written_content
            assert "## Baseline vs Tools Comparison" in written_content
            assert "## Performance by Task" in written_content
            assert "## Performance by Model" in written_content
            assert "## Error Analysis" in written_content
    
    def test_generate_csv_report(self, report_generator, sample_benchmark_data):
        """Test generating CSV format report."""
        # Add sample results for CSV generation
        sample_benchmark_data["results"] = [
            {
                "task_id": "task1",
                "approach": "baseline",
                "model_instance": "small",
                "status": "completed",
                "duration": 2.0,
                "input_tokens": 100,
                "output_tokens": 200,
                "total_tokens": 300,
                "sample_num": 1,
                "start_time": 1234567890.0,
                "end_time": 1234567892.0,
                "error": None
            },
            {
                "task_id": "task1",
                "approach": "tools",
                "model_instance": "small",
                "status": "completed",
                "duration": 1.5,
                "input_tokens": 80,
                "output_tokens": 150,
                "total_tokens": 230,
                "sample_num": 1,
                "start_time": 1234567895.0,
                "end_time": 1234567896.5,
                "error": None
            }
        ]
        
        with patch("builtins.open", mock_open()) as mock_file:
            result_path = report_generator.generate_report(
                sample_benchmark_data,
                OutputFormat.CSV,
                "test_report"
            )
            
            assert result_path.endswith("test_report.csv")
            mock_file.assert_called_once()
            
            # Check that CSV content was written
            handle = mock_file()
            written_content = "".join(call.args[0] for call in handle.write.call_args_list)
            
            assert "task_id,approach,model_instance,status,duration" in written_content
            assert "task1,baseline,small,completed,2.0" in written_content
            assert "task1,tools,small,completed,1.5" in written_content
    
    def test_generate_console_report(self, report_generator, sample_benchmark_data):
        """Test generating console format report."""
        result = report_generator.generate_report(
            sample_benchmark_data,
            OutputFormat.CONSOLE,
            "test_report"
        )
        
        # Console format returns content directly
        assert "🚀 AI Development Tools Benchmark Report" in result
        assert "Profile: MEDIUM" in result
        assert "📊 Overall Performance:" in result
        assert "🎯 Baseline vs Tools:" in result
        assert "📋 Task Performance:" in result
        assert "🤖 Model Performance:" in result
        assert "Success Rate: 100.0%" in result
        assert "Token Reduction: 25.0%" in result
        assert "Time Reduction: 30.0%" in result
    
    def test_generate_performance_dashboard(self, report_generator, sample_benchmark_data):
        """Test generating ASCII performance dashboard."""
        dashboard = report_generator.generate_performance_dashboard(sample_benchmark_data)
        
        assert "┌─────────────────────────────────────────────────────────────┐" in dashboard
        assert "│                 Performance Dashboard                       │" in dashboard
        assert "Success Rate:" in dashboard
        assert "Avg Duration:" in dashboard
        assert "Throughput:" in dashboard
        assert "Token Reduction:" in dashboard
        assert "Time Reduction:" in dashboard
        assert "└─────────────────────────────────────────────────────────────┘" in dashboard
    
    def test_create_bar(self, report_generator):
        """Test ASCII progress bar creation."""
        # Test different values
        bar_full = report_generator._create_bar(1.0, 0.5)
        assert bar_full == "[████████████████████]"
        
        bar_half = report_generator._create_bar(0.5, 0.3)
        assert bar_half == "[██████████░░░░░░░░░░]"
        
        bar_empty = report_generator._create_bar(0.0, 0.5)
        assert bar_empty == "[░░░░░░░░░░░░░░░░░░░░]"
        
        bar_threshold = report_generator._create_bar(0.2, 0.5)
        assert bar_threshold == "[▓▓▓▓░░░░░░░░░░░░░░░░]"
    
    def test_generate_comparison_chart(self, report_generator, sample_benchmark_data):
        """Test generating comparison chart."""
        comparison_chart = report_generator.generate_comparison_chart(
            sample_benchmark_data["comparison_metrics"]
        )
        
        assert "┌─────────────────────────────────────────────────────────────┐" in comparison_chart
        assert "│                 Baseline vs Tools                           │" in comparison_chart
        assert "Duration" in comparison_chart
        assert "Tokens" in comparison_chart
        assert "Success Rate" in comparison_chart
        assert "Throughput" in comparison_chart
        assert "Baseline:" in comparison_chart
        assert "Tools:" in comparison_chart
        assert "Winner:" in comparison_chart
        assert "Improvement:" in comparison_chart
        assert "└─────────────────────────────────────────────────────────────┘" in comparison_chart
    
    def test_generate_trend_analysis(self, report_generator):
        """Test generating trend analysis."""
        historical_data = [
            {
                "benchmark_info": {"timestamp": 1234567890.0},
                "comparison_metrics": {
                    "token_reduction_percent": 20.0,
                    "time_reduction_percent": 25.0
                },
                "overall_metrics": {"success_rate": 0.85}
            },
            {
                "benchmark_info": {"timestamp": 1234567950.0},
                "comparison_metrics": {
                    "token_reduction_percent": 25.0,
                    "time_reduction_percent": 30.0
                },
                "overall_metrics": {"success_rate": 0.90}
            },
            {
                "benchmark_info": {"timestamp": 1234568000.0},
                "comparison_metrics": {
                    "token_reduction_percent": 30.0,
                    "time_reduction_percent": 35.0
                },
                "overall_metrics": {"success_rate": 0.95}
            }
        ]
        
        trend_analysis = report_generator.generate_trend_analysis(historical_data)
        
        assert "📈 Trend Analysis" in trend_analysis
        assert "Token Reduction Trend:" in trend_analysis
        assert "Time Reduction Trend:" in trend_analysis
        assert "Success Rate Trend:" in trend_analysis
        assert "Improving ↗" in trend_analysis
        assert "📊 Change Since First Run:" in trend_analysis
    
    def test_calculate_trend(self, report_generator):
        """Test trend calculation."""
        # Test improving trend
        improving_trend = report_generator._calculate_trend([10.0, 15.0, 20.0])
        assert improving_trend == "Improving ↗"
        
        # Test declining trend
        declining_trend = report_generator._calculate_trend([20.0, 15.0, 10.0])
        assert declining_trend == "Declining ↘"
        
        # Test stable trend
        stable_trend = report_generator._calculate_trend([15.0, 15.05, 15.02])
        assert stable_trend == "Stable"
        
        # Test insufficient data
        no_trend = report_generator._calculate_trend([10.0])
        assert no_trend == "No trend data"
    
    def test_generate_batch_report(self, report_generator, sample_benchmark_data):
        """Test generating batch report."""
        batch_results = [
            sample_benchmark_data,
            {
                **sample_benchmark_data,
                "benchmark_info": {
                    **sample_benchmark_data["benchmark_info"],
                    "profile": "heavy"
                }
            }
        ]
        
        with patch("builtins.open", mock_open()) as mock_file:
            result_path = report_generator.generate_batch_report(
                batch_results,
                OutputFormat.JSON,
                "batch_report"
            )
            
            assert result_path.endswith("batch_report.json")
            mock_file.assert_called_once()
    
    def test_generate_batch_markdown_report(self, report_generator, sample_benchmark_data):
        """Test generating batch markdown report."""
        batch_data = {
            "batch_results": [sample_benchmark_data],
            "aggregated_stats": {
                "token_reduction": {
                    "mean": 25.0,
                    "median": 25.0,
                    "std": 0.0,
                    "min": 25.0,
                    "max": 25.0
                },
                "time_reduction": {
                    "mean": 30.0,
                    "median": 30.0,
                    "std": 0.0,
                    "min": 30.0,
                    "max": 30.0
                }
            },
            "summary": {
                "total_runs": 1,
                "successful_runs": 1
            }
        }
        
        markdown_report = report_generator._generate_batch_markdown_report(batch_data)
        
        assert "# Batch Benchmark Report" in markdown_report
        assert "**Total Runs:** 1" in markdown_report
        assert "**Successful Runs:** 1" in markdown_report
        assert "## Aggregated Statistics" in markdown_report
        assert "### Token Reduction" in markdown_report
        assert "### Time Reduction" in markdown_report
        assert "## Individual Results" in markdown_report
    
    def test_aggregate_batch_data(self, report_generator, sample_benchmark_data):
        """Test aggregating batch data."""
        batch_results = [
            sample_benchmark_data,
            {
                **sample_benchmark_data,
                "comparison_metrics": {
                    **sample_benchmark_data["comparison_metrics"],
                    "token_reduction_percent": 35.0,
                    "time_reduction_percent": 40.0,
                    "efficiency_improvement_percent": 20.0
                }
            }
        ]
        
        aggregated = report_generator._aggregate_batch_data(batch_results)
        
        assert "batch_results" in aggregated
        assert "aggregated_stats" in aggregated
        assert "summary" in aggregated
        
        stats = aggregated["aggregated_stats"]
        assert "token_reduction" in stats
        assert "time_reduction" in stats
        assert "efficiency_improvement" in stats
        
        # Check mean calculations
        assert stats["token_reduction"]["mean"] == 30.0  # (25.0 + 35.0) / 2
        assert stats["time_reduction"]["mean"] == 35.0   # (30.0 + 40.0) / 2
        assert stats["efficiency_improvement"]["mean"] == 17.5  # (15.0 + 20.0) / 2
    
    def test_create_summary_table(self, report_generator, sample_benchmark_data):
        """Test creating summary table."""
        batch_results = [
            {
                **sample_benchmark_data,
                "batch_info": {
                    "name": "quick",
                    "profile": "light"
                }
            },
            {
                "batch_info": {
                    "name": "standard",
                    "profile": "medium"
                },
                "error": "Connection failed"
            }
        ]
        
        summary_table = report_generator.create_summary_table(batch_results)
        
        assert "| Configuration | Profile | Status | Token Reduction | Time Reduction | Efficiency |" in summary_table
        assert "| quick | light | Success | 25.0% | 30.0% | 15.0% |" in summary_table
        assert "| standard | medium | Failed | N/A | N/A | N/A |" in summary_table
    
    def test_export_raw_data(self, report_generator, sample_benchmark_data):
        """Test exporting raw data."""
        with patch("builtins.open", mock_open()) as mock_file:
            result_path = report_generator.export_raw_data(
                sample_benchmark_data,
                "raw_export"
            )
            
            assert result_path.endswith("raw_export.json")
            mock_file.assert_called_once()
            
            # Check that JSON content was written
            handle = mock_file()
            written_content = "".join(call.args[0] for call in handle.write.call_args_list)
            parsed_content = json.loads(written_content)
            
            assert parsed_content["benchmark_info"]["profile"] == "medium"
    
    def test_report_generator_initialization(self):
        """Test report generator initialization."""
        with patch("pathlib.Path.mkdir") as mock_mkdir:
            generator = ReportGenerator("/custom/output/path")
            
            assert generator.output_dir == Path("/custom/output/path")
            mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)
    
    def test_auto_filename_generation(self, report_generator, sample_benchmark_data):
        """Test automatic filename generation."""
        with patch("builtins.open", mock_open()) as mock_file:
            with patch("ai_dev_tools.benchmark.reporting.datetime") as mock_datetime:
                mock_datetime.now.return_value.strftime.return_value = "20240101_120000"
                
                result_path = report_generator.generate_report(
                    sample_benchmark_data,
                    OutputFormat.JSON,
                    filename=None  # Should auto-generate
                )
                
                assert "benchmark_medium_20240101_120000.json" in result_path
                mock_file.assert_called_once()
    
    def test_unsupported_format_error(self, report_generator, sample_benchmark_data):
        """Test error handling for unsupported format."""
        with pytest.raises(ValueError, match="Unsupported format"):
            report_generator.generate_report(
                sample_benchmark_data,
                "unsupported_format",
                "test_report"
            )
    
    def test_no_results_csv(self, report_generator):
        """Test CSV generation with no results."""
        empty_data = {"results": []}
        
        csv_content = report_generator._generate_csv_report(empty_data)
        assert csv_content == "No results found"
    
    def test_minimal_data_handling(self, report_generator):
        """Test handling of minimal data structures."""
        minimal_data = {
            "benchmark_info": {"profile": "test"},
            "overall_metrics": {},
            "comparison_metrics": {}
        }
        
        # Should not raise exceptions
        console_report = report_generator._generate_console_report(minimal_data)
        assert "Profile: TEST" in console_report
        
        markdown_report = report_generator._generate_markdown_report(minimal_data)
        assert "**Profile:** TEST" in markdown_report