#!/usr/bin/env python3
"""
Batch Results Analyzer

Analyzes and compares results from multiple batch benchmark runs
for comprehensive performance insights and trend analysis.
"""

import argparse
import json
import statistics
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import matplotlib.pyplot as plt
import pandas as pd


class BatchResultsAnalyzer:
    def __init__(self, results_dir: str = "batch_results"):
        self.results_dir = Path(results_dir)
        self.results = []

    def load_batch_files(self, pattern: str = "batch_*.json") -> List[Dict[str, Any]]:
        """Load all batch result files matching pattern"""

        files = list(self.results_dir.glob(pattern))
        loaded_results = []

        print(f"📁 Found {len(files)} batch result files")

        for file_path in sorted(files):
            try:
                with open(file_path) as f:
                    data = json.load(f)
                    data["_file_path"] = str(file_path)
                    data["_file_name"] = file_path.name
                    loaded_results.append(data)
                    print(f"   ✅ Loaded: {file_path.name}")
            except Exception as e:
                print(f"   ❌ Failed to load {file_path.name}: {e}")

        self.results = loaded_results
        return loaded_results

    def analyze_performance_trends(self) -> Dict[str, Any]:
        """Analyze performance trends across batch runs"""

        trends = {"by_batch_type": {}, "by_profile": {}, "by_model": {}, "temporal": []}

        for result in self.results:
            batch_info = result.get("batch_info", {})
            batch_name = batch_info.get("batch_name", "unknown")
            timestamp = batch_info.get("timestamp", "")

            # Extract successful configurations
            successful_configs = [config for config in result.get("configurations", []) if config.get("success", False)]

            for config in successful_configs:
                config_info = config.get("config", {})
                profile = config_info.get("profile", "unknown")

                results_data = config.get("results", {})
                improvements = results_data.get("improvements", {})

                # Process each model's improvements
                for model, stats in improvements.items():
                    token_reduction = stats.get("token_reduction_percent", 0)
                    time_reduction = stats.get("time_reduction_percent", 0)

                    # By batch type
                    if batch_name not in trends["by_batch_type"]:
                        trends["by_batch_type"][batch_name] = []
                    trends["by_batch_type"][batch_name].append(
                        {
                            "token_reduction": token_reduction,
                            "time_reduction": time_reduction,
                            "model": model,
                            "profile": profile,
                        }
                    )

                    # By profile
                    if profile not in trends["by_profile"]:
                        trends["by_profile"][profile] = []
                    trends["by_profile"][profile].append(
                        {
                            "token_reduction": token_reduction,
                            "time_reduction": time_reduction,
                            "model": model,
                            "batch": batch_name,
                        }
                    )

                    # By model
                    if model not in trends["by_model"]:
                        trends["by_model"][model] = []
                    trends["by_model"][model].append(
                        {
                            "token_reduction": token_reduction,
                            "time_reduction": time_reduction,
                            "profile": profile,
                            "batch": batch_name,
                        }
                    )

                    # Temporal data
                    trends["temporal"].append(
                        {
                            "timestamp": timestamp,
                            "batch": batch_name,
                            "profile": profile,
                            "model": model,
                            "token_reduction": token_reduction,
                            "time_reduction": time_reduction,
                        }
                    )

        return trends

    def generate_summary_report(self, trends: Dict[str, Any]) -> str:
        """Generate a comprehensive summary report"""

        report = []
        report.append("# AI Development Tools - Batch Results Analysis")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Total batch files analyzed: {len(self.results)}")
        report.append("")

        # Overall Statistics
        all_token_reductions = []
        all_time_reductions = []

        for batch_data in trends["by_batch_type"].values():
            all_token_reductions.extend([d["token_reduction"] for d in batch_data])
            all_time_reductions.extend([d["time_reduction"] for d in batch_data])

        if all_token_reductions:
            report.append("## Overall Performance Summary")
            report.append(f"- **Average token reduction**: {statistics.mean(all_token_reductions):.1f}%")
            report.append(f"- **Median token reduction**: {statistics.median(all_token_reductions):.1f}%")
            report.append(f"- **Token reduction std dev**: {statistics.stdev(all_token_reductions):.1f}%")
            report.append(f"- **Average time reduction**: {statistics.mean(all_time_reductions):.1f}%")
            report.append(f"- **Median time reduction**: {statistics.median(all_time_reductions):.1f}%")
            report.append(f"- **Total data points**: {len(all_token_reductions)}")
            report.append("")

        # By Batch Type
        if trends["by_batch_type"]:
            report.append("## Performance by Batch Type")
            for batch_type, data in trends["by_batch_type"].items():
                token_avg = statistics.mean([d["token_reduction"] for d in data])
                time_avg = statistics.mean([d["time_reduction"] for d in data])
                report.append(
                    f"- **{batch_type}**: {token_avg:.1f}% tokens, {time_avg:.1f}% time ({len(data)} samples)"
                )
            report.append("")

        # By Profile
        if trends["by_profile"]:
            report.append("## Performance by Hardware Profile")
            for profile, data in trends["by_profile"].items():
                token_avg = statistics.mean([d["token_reduction"] for d in data])
                time_avg = statistics.mean([d["time_reduction"] for d in data])
                report.append(f"- **{profile}**: {token_avg:.1f}% tokens, {time_avg:.1f}% time ({len(data)} samples)")
            report.append("")

        # By Model
        if trends["by_model"]:
            report.append("## Performance by Model")
            for model, data in trends["by_model"].items():
                token_avg = statistics.mean([d["token_reduction"] for d in data])
                time_avg = statistics.mean([d["time_reduction"] for d in data])
                report.append(f"- **{model}**: {token_avg:.1f}% tokens, {time_avg:.1f}% time ({len(data)} samples)")
            report.append("")

        # Key Insights
        report.append("## Key Insights")

        if trends["by_profile"]:
            # Find best performing profile
            profile_performance = {}
            for profile, data in trends["by_profile"].items():
                profile_performance[profile] = statistics.mean([d["token_reduction"] for d in data])

            best_profile = max(profile_performance.keys(), key=lambda x: profile_performance[x])
            report.append(
                f"- **Best performing profile**: {best_profile} ({profile_performance[best_profile]:.1f}% token reduction)"
            )

        if trends["by_model"]:
            # Find best performing model
            model_performance = {}
            for model, data in trends["by_model"].items():
                model_performance[model] = statistics.mean([d["token_reduction"] for d in data])

            best_model = max(model_performance.keys(), key=lambda x: model_performance[x])
            report.append(
                f"- **Best performing model**: {best_model} ({model_performance[best_model]:.1f}% token reduction)"
            )

        # Consistency analysis
        if all_token_reductions:
            cv = (statistics.stdev(all_token_reductions) / statistics.mean(all_token_reductions)) * 100
            report.append(f"- **Performance consistency**: {cv:.1f}% coefficient of variation")

        return "\\n".join(report)

    def export_csv_data(self, trends: Dict[str, Any], output_file: str = "batch_analysis.csv"):
        """Export trend data to CSV for further analysis"""

        if not trends["temporal"]:
            print("❌ No temporal data available for CSV export")
            return

        df = pd.DataFrame(trends["temporal"])
        df.to_csv(output_file, index=False)
        print(f"📊 CSV data exported to: {output_file}")

    def create_visualizations(self, trends: Dict[str, Any], output_dir: str = "visualizations"):
        """Create performance visualization charts"""

        viz_dir = Path(output_dir)
        viz_dir.mkdir(exist_ok=True)

        try:
            # Performance by profile
            if trends["by_profile"]:
                profiles = list(trends["by_profile"].keys())
                token_avgs = [
                    statistics.mean([d["token_reduction"] for d in trends["by_profile"][p]]) for p in profiles
                ]
                time_avgs = [statistics.mean([d["time_reduction"] for d in trends["by_profile"][p]]) for p in profiles]

                fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

                ax1.bar(profiles, token_avgs)
                ax1.set_title("Token Reduction by Profile")
                ax1.set_ylabel("Reduction %")

                ax2.bar(profiles, time_avgs)
                ax2.set_title("Time Reduction by Profile")
                ax2.set_ylabel("Reduction %")

                plt.tight_layout()
                plt.savefig(viz_dir / "performance_by_profile.png", dpi=150, bbox_inches="tight")
                plt.close()

                print(f"📈 Visualization saved: {viz_dir}/performance_by_profile.png")

        except ImportError:
            print("⚠️  matplotlib not available - skipping visualizations")
            print("   Install with: uv add matplotlib pandas")


def main():
    parser = argparse.ArgumentParser(description="AI Development Tools Batch Results Analyzer")
    parser.add_argument(
        "--results-dir",
        default="batch_results",
        help="Directory containing batch result files",
    )
    parser.add_argument(
        "--pattern",
        default="batch_*.json",
        help="File pattern to match (default: batch_*.json)",
    )
    parser.add_argument(
        "--output-report",
        default="batch_analysis_report.md",
        help="Output file for summary report",
    )
    parser.add_argument("--export-csv", action="store_true", help="Export data to CSV")
    parser.add_argument("--create-visualizations", action="store_true", help="Create performance charts")

    args = parser.parse_args()

    print("📊 AI Development Tools Batch Results Analyzer")
    print("=" * 60)

    # Initialize analyzer
    analyzer = BatchResultsAnalyzer(args.results_dir)

    # Load results
    results = analyzer.load_batch_files(args.pattern)
    if not results:
        print("❌ No batch result files found!")
        return

    # Analyze trends
    print("\n🔍 Analyzing performance trends...")
    trends = analyzer.analyze_performance_trends()

    # Generate report
    print("📝 Generating summary report...")
    report = analyzer.generate_summary_report(trends)

    with open(args.output_report, "w") as f:
        f.write(report)
    print(f"✅ Report saved to: {args.output_report}")

    # Optional exports
    if args.export_csv:
        analyzer.export_csv_data(trends)

    if args.create_visualizations:
        analyzer.create_visualizations(trends)

    # Display quick summary
    print("\n📊 QUICK SUMMARY")
    print("=" * 40)
    print(f"Batch files processed: {len(results)}")
    print(f"Batch types found: {len(trends['by_batch_type'])}")
    print(f"Hardware profiles: {len(trends['by_profile'])}")
    print(f"Models tested: {len(trends['by_model'])}")


if __name__ == "__main__":
    main()
