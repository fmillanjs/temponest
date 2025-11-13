#!/usr/bin/env python3
"""
Aggregate Performance Test Results

Collects and analyzes results from all performance tests:
- Locust load tests
- K6 load tests
- Database benchmarks
- Docker startup measurements

Generates a comprehensive performance validation report.
"""

import json
import glob
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
import statistics


class PerformanceAggregator:
    """Aggregates performance test results"""

    def __init__(self, reports_dir: str):
        self.reports_dir = Path(reports_dir)
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "locust": {},
            "k6": {},
            "database": {},
            "docker": {},
            "summary": {}
        }

    def parse_locust_results(self):
        """Parse Locust test results from reports"""
        print("Parsing Locust results...")

        locust_files = glob.glob(str(self.reports_dir / "locust-*.html"))
        txt_files = glob.glob(str(self.reports_dir / "locust-*.txt"))

        if txt_files:
            # Parse the most recent text output
            latest_txt = max(txt_files, key=os.path.getctime)
            with open(latest_txt, 'r') as f:
                content = f.read()

            # Extract key metrics from text output
            self.results["locust"] = {
                "test_file": latest_txt,
                "status": "completed" if "Aggregated" in content else "failed",
                "html_reports": locust_files,
            }
        else:
            self.results["locust"] = {"status": "not_run"}

    def parse_k6_results(self):
        """Parse K6 test results"""
        print("Parsing K6 results...")

        k6_json = glob.glob(str(self.reports_dir / "k6-*-summary.json"))
        k6_txt = glob.glob(str(self.reports_dir / "k6-*.txt"))

        results = []
        for json_file in k6_json:
            try:
                with open(json_file, 'r') as f:
                    data = json.load(f)
                results.append({
                    "file": json_file,
                    "test_name": os.path.basename(json_file),
                    "metrics": data.get("metrics", {})
                })
            except Exception as e:
                print(f"Error parsing {json_file}: {e}")

        self.results["k6"] = {
            "tests": results,
            "count": len(results),
            "status": "completed" if results else "not_run"
        }

    def parse_database_results(self):
        """Parse database benchmark results"""
        print("Parsing database benchmark results...")

        db_json = glob.glob(str(self.reports_dir / "db-benchmark*.json"))

        if db_json:
            latest_db = max(db_json, key=os.path.getctime)
            try:
                with open(latest_db, 'r') as f:
                    data = json.load(f)

                self.results["database"] = {
                    "file": latest_db,
                    "summary": data.get("summary", {}),
                    "test_count": len(data.get("results", [])),
                    "status": "completed"
                }

                # Extract key metrics
                if "summary" in data:
                    summary = data["summary"]
                    self.results["database"]["metrics"] = {
                        "total_queries": summary.get("total_queries", 0),
                        "avg_time_ms": summary.get("overall_avg_time", 0),
                        "avg_qps": summary.get("overall_avg_qps", 0),
                        "total_errors": summary.get("total_errors", 0)
                    }

            except Exception as e:
                print(f"Error parsing database results: {e}")
                self.results["database"] = {"status": "error", "error": str(e)}
        else:
            self.results["database"] = {"status": "not_run"}

    def parse_docker_results(self):
        """Parse Docker startup measurement results"""
        print("Parsing Docker startup results...")

        docker_json = glob.glob(str(self.reports_dir / "docker-startup*.json"))

        if docker_json:
            latest_docker = max(docker_json, key=os.path.getctime)
            try:
                with open(latest_docker, 'r') as f:
                    data = json.load(f)

                summary = data.get("summary", {})
                self.results["docker"] = {
                    "file": latest_docker,
                    "status": "completed",
                    "metrics": {
                        "total_time": summary.get("total_time", 0),
                        "compose_time": summary.get("compose_time", 0),
                        "avg_health_time": summary.get("average_health_time", 0),
                        "healthy_containers": summary.get("healthy_containers", 0),
                        "total_containers": summary.get("total_containers", 0)
                    }
                }

            except Exception as e:
                print(f"Error parsing Docker results: {e}")
                self.results["docker"] = {"status": "error", "error": str(e)}
        else:
            self.results["docker"] = {"status": "not_run"}

    def generate_summary(self):
        """Generate overall performance summary"""
        print("Generating summary...")

        summary = {
            "tests_run": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "performance_grade": "Unknown",
            "issues": [],
            "highlights": []
        }

        # Count test statuses
        for test_type in ["locust", "k6", "database", "docker"]:
            if self.results[test_type].get("status") == "completed":
                summary["tests_run"] += 1
                summary["tests_passed"] += 1
            elif self.results[test_type].get("status") == "failed":
                summary["tests_run"] += 1
                summary["tests_failed"] += 1
                summary["issues"].append(f"{test_type.title()} tests failed")

        # Evaluate performance
        if summary["tests_passed"] == summary["tests_run"] and summary["tests_run"] > 0:
            summary["performance_grade"] = "Excellent"
            summary["highlights"].append("All performance tests passed")
        elif summary["tests_passed"] >= summary["tests_run"] * 0.75:
            summary["performance_grade"] = "Good"
        elif summary["tests_passed"] >= summary["tests_run"] * 0.5:
            summary["performance_grade"] = "Fair"
        else:
            summary["performance_grade"] = "Poor"

        # Check specific metrics
        if self.results["database"].get("status") == "completed":
            db_metrics = self.results["database"].get("metrics", {})
            avg_time = db_metrics.get("avg_time_ms", 0)
            if avg_time > 0 and avg_time < 10:
                summary["highlights"].append(f"Database avg response time: {avg_time:.2f}ms (Excellent)")
            elif avg_time > 50:
                summary["issues"].append(f"Database avg response time: {avg_time:.2f}ms (High)")

        if self.results["docker"].get("status") == "completed":
            docker_metrics = self.results["docker"].get("metrics", {})
            total_time = docker_metrics.get("total_time", 0)
            if total_time > 0 and total_time < 60:
                summary["highlights"].append(f"Docker startup time: {total_time:.1f}s (Fast)")
            elif total_time > 90:
                summary["issues"].append(f"Docker startup time: {total_time:.1f}s (Slow)")

        self.results["summary"] = summary

    def save_results(self, output_file: str):
        """Save aggregated results to JSON"""
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump(self.results, f, indent=2)

        print(f"\n✓ Aggregated results saved to: {output_file}")

    def print_summary(self):
        """Print summary to console"""
        print("\n" + "=" * 80)
        print("PERFORMANCE VALIDATION SUMMARY")
        print("=" * 80)

        summary = self.results["summary"]

        print(f"\nTimestamp: {self.results['timestamp']}")
        print(f"Performance Grade: {summary['performance_grade']}")
        print(f"\nTests Run: {summary['tests_run']}")
        print(f"Tests Passed: {summary['tests_passed']}")
        print(f"Tests Failed: {summary['tests_failed']}")

        if summary["highlights"]:
            print("\nHighlights:")
            for highlight in summary["highlights"]:
                print(f"  ✓ {highlight}")

        if summary["issues"]:
            print("\nIssues:")
            for issue in summary["issues"]:
                print(f"  ✗ {issue}")

        print("\n" + "-" * 80)
        print("Test Results by Type:")
        print("-" * 80)

        for test_type in ["locust", "k6", "database", "docker"]:
            status = self.results[test_type].get("status", "unknown")
            status_symbol = "✓" if status == "completed" else ("✗" if status == "failed" else "○")
            print(f"{status_symbol} {test_type.title()}: {status}")

            if test_type == "database" and status == "completed":
                metrics = self.results[test_type].get("metrics", {})
                print(f"    Avg Response Time: {metrics.get('avg_time_ms', 0):.2f}ms")
                print(f"    Avg Throughput: {metrics.get('avg_qps', 0):.1f} qps")

            elif test_type == "docker" and status == "completed":
                metrics = self.results[test_type].get("metrics", {})
                print(f"    Total Startup Time: {metrics.get('total_time', 0):.1f}s")
                print(f"    Healthy Containers: {metrics.get('healthy_containers', 0)}/{metrics.get('total_containers', 0)}")

        print("=" * 80)

    def run(self):
        """Run all aggregation tasks"""
        self.parse_locust_results()
        self.parse_k6_results()
        self.parse_database_results()
        self.parse_docker_results()
        self.generate_summary()


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Aggregate performance test results')
    parser.add_argument('--reports-dir', default='tests/performance/reports',
                        help='Directory containing test reports')
    parser.add_argument('--output', default='tests/performance/reports/aggregated-results.json',
                        help='Output file for aggregated results')

    args = parser.parse_args()

    print("=" * 80)
    print("Performance Results Aggregator")
    print("=" * 80)
    print(f"\nReports Directory: {args.reports_dir}")
    print(f"Output File: {args.output}")

    aggregator = PerformanceAggregator(args.reports_dir)
    aggregator.run()
    aggregator.print_summary()
    aggregator.save_results(args.output)


if __name__ == "__main__":
    main()
