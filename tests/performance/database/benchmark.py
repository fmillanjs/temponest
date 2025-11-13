"""
Database Performance Benchmarking Suite for TempoNest

Tests database performance including:
- Connection pool performance
- Query execution times
- Index effectiveness
- Concurrent query handling
- Cache hit rates

Usage:
    python tests/performance/database/benchmark.py
    python tests/performance/database/benchmark.py --verbose
    python tests/performance/database/benchmark.py --output reports/db-benchmark.json
"""

import asyncio
import asyncpg
import time
import statistics
import json
import argparse
from datetime import datetime
from typing import List, Dict, Any
from dataclasses import dataclass, asdict


@dataclass
class BenchmarkResult:
    """Results from a benchmark test"""
    test_name: str
    total_queries: int
    total_time: float
    avg_time: float
    median_time: float
    p95_time: float
    p99_time: float
    min_time: float
    max_time: float
    queries_per_second: float
    success_rate: float
    errors: int

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class DatabaseBenchmark:
    """Database performance benchmarking tool"""

    def __init__(self, connection_string: str, verbose: bool = False):
        self.connection_string = connection_string
        self.verbose = verbose
        self.results: List[BenchmarkResult] = []
        self.pool = None

    async def setup(self):
        """Setup database connection pool"""
        if self.verbose:
            print("Setting up database connection pool...")

        self.pool = await asyncpg.create_pool(
            self.connection_string,
            min_size=10,
            max_size=20,
            command_timeout=60,
        )

        if self.verbose:
            print("✓ Connection pool ready")

    async def cleanup(self):
        """Cleanup database connections"""
        if self.pool:
            await self.pool.close()
            if self.verbose:
                print("✓ Connection pool closed")

    async def run_query_benchmark(
        self,
        name: str,
        query: str,
        iterations: int = 1000,
        params: tuple = None
    ) -> BenchmarkResult:
        """Run a benchmark for a specific query"""
        if self.verbose:
            print(f"\nRunning: {name}")
            print(f"  Query: {query}")
            print(f"  Iterations: {iterations}")

        times = []
        errors = 0
        start_time = time.time()

        for i in range(iterations):
            try:
                query_start = time.time()
                async with self.pool.acquire() as conn:
                    if params:
                        await conn.fetch(query, *params)
                    else:
                        await conn.fetch(query)
                query_time = (time.time() - query_start) * 1000  # Convert to ms
                times.append(query_time)

                if self.verbose and (i + 1) % 100 == 0:
                    print(f"  Progress: {i + 1}/{iterations}")

            except Exception as e:
                errors += 1
                if self.verbose:
                    print(f"  Error: {e}")

        total_time = time.time() - start_time

        # Calculate statistics
        if times:
            times.sort()
            result = BenchmarkResult(
                test_name=name,
                total_queries=iterations,
                total_time=total_time,
                avg_time=statistics.mean(times),
                median_time=statistics.median(times),
                p95_time=times[int(len(times) * 0.95)] if times else 0,
                p99_time=times[int(len(times) * 0.99)] if times else 0,
                min_time=min(times),
                max_time=max(times),
                queries_per_second=iterations / total_time if total_time > 0 else 0,
                success_rate=(iterations - errors) / iterations * 100 if iterations > 0 else 0,
                errors=errors
            )
        else:
            result = BenchmarkResult(
                test_name=name,
                total_queries=iterations,
                total_time=total_time,
                avg_time=0,
                median_time=0,
                p95_time=0,
                p99_time=0,
                min_time=0,
                max_time=0,
                queries_per_second=0,
                success_rate=0,
                errors=errors
            )

        self.results.append(result)

        if self.verbose:
            print(f"  ✓ Completed in {total_time:.2f}s")
            print(f"  Avg: {result.avg_time:.2f}ms, P95: {result.p95_time:.2f}ms")

        return result

    async def run_concurrent_benchmark(
        self,
        name: str,
        query: str,
        concurrent_queries: int = 50,
        iterations_per_worker: int = 20
    ) -> BenchmarkResult:
        """Run concurrent queries to test connection pool"""
        if self.verbose:
            print(f"\nRunning: {name}")
            print(f"  Concurrent: {concurrent_queries}")
            print(f"  Iterations per worker: {iterations_per_worker}")

        times = []
        errors = 0
        start_time = time.time()

        async def worker():
            nonlocal errors
            for _ in range(iterations_per_worker):
                try:
                    query_start = time.time()
                    async with self.pool.acquire() as conn:
                        await conn.fetch(query)
                    query_time = (time.time() - query_start) * 1000
                    times.append(query_time)
                except Exception:
                    errors += 1

        # Run concurrent workers
        await asyncio.gather(*[worker() for _ in range(concurrent_queries)])

        total_time = time.time() - start_time
        total_queries = concurrent_queries * iterations_per_worker

        # Calculate statistics
        if times:
            times.sort()
            result = BenchmarkResult(
                test_name=name,
                total_queries=total_queries,
                total_time=total_time,
                avg_time=statistics.mean(times),
                median_time=statistics.median(times),
                p95_time=times[int(len(times) * 0.95)] if times else 0,
                p99_time=times[int(len(times) * 0.99)] if times else 0,
                min_time=min(times),
                max_time=max(times),
                queries_per_second=total_queries / total_time if total_time > 0 else 0,
                success_rate=(total_queries - errors) / total_queries * 100 if total_queries > 0 else 0,
                errors=errors
            )
        else:
            result = BenchmarkResult(
                test_name=name,
                total_queries=total_queries,
                total_time=total_time,
                avg_time=0,
                median_time=0,
                p95_time=0,
                p99_time=0,
                min_time=0,
                max_time=0,
                queries_per_second=0,
                success_rate=0,
                errors=errors
            )

        self.results.append(result)

        if self.verbose:
            print(f"  ✓ Completed in {total_time:.2f}s")
            print(f"  Throughput: {result.queries_per_second:.2f} qps")

        return result

    async def benchmark_simple_queries(self):
        """Benchmark simple SELECT queries"""
        print("\n=== Simple Query Benchmarks ===")

        # Test 1: Simple health check query
        await self.run_query_benchmark(
            "Health Check Query",
            "SELECT 1",
            iterations=1000
        )

        # Test 2: Current timestamp
        await self.run_query_benchmark(
            "Timestamp Query",
            "SELECT NOW()",
            iterations=1000
        )

        # Test 3: Count query (agents table)
        await self.run_query_benchmark(
            "Count Query (Agents)",
            "SELECT COUNT(*) FROM agents",
            iterations=1000
        )

        # Test 4: Count query (schedules table)
        await self.run_query_benchmark(
            "Count Query (Schedules)",
            "SELECT COUNT(*) FROM schedules",
            iterations=1000
        )

    async def benchmark_indexed_queries(self):
        """Benchmark queries that use indexes"""
        print("\n=== Indexed Query Benchmarks ===")

        # Test 1: Query by ID (primary key)
        await self.run_query_benchmark(
            "Query by ID (Primary Key)",
            "SELECT * FROM agents WHERE id = $1 LIMIT 1",
            iterations=1000,
            params=(1,)
        )

        # Test 2: Query by tenant_id (indexed)
        await self.run_query_benchmark(
            "Query by Tenant ID (Index)",
            "SELECT * FROM agents WHERE tenant_id = $1 LIMIT 10",
            iterations=1000,
            params=('test-tenant',)
        )

        # Test 3: Query by created_at (indexed)
        await self.run_query_benchmark(
            "Query by Created At (Index)",
            "SELECT * FROM agents WHERE created_at > NOW() - INTERVAL '7 days' LIMIT 100",
            iterations=1000
        )

    async def benchmark_joins(self):
        """Benchmark JOIN queries"""
        print("\n=== JOIN Query Benchmarks ===")

        # Test 1: Simple JOIN (schedules + agents)
        await self.run_query_benchmark(
            "Simple JOIN (Schedules + Agents)",
            """
            SELECT s.*, a.name as agent_name
            FROM schedules s
            JOIN agents a ON s.agent_id = a.id
            LIMIT 100
            """,
            iterations=500
        )

        # Test 2: JOIN with WHERE clause
        await self.run_query_benchmark(
            "JOIN with Filter",
            """
            SELECT s.*, a.name as agent_name
            FROM schedules s
            JOIN agents a ON s.agent_id = a.id
            WHERE s.is_active = true
            LIMIT 100
            """,
            iterations=500
        )

    async def benchmark_aggregations(self):
        """Benchmark aggregation queries"""
        print("\n=== Aggregation Query Benchmarks ===")

        # Test 1: Count by tenant
        await self.run_query_benchmark(
            "Count by Tenant",
            """
            SELECT tenant_id, COUNT(*) as count
            FROM agents
            GROUP BY tenant_id
            """,
            iterations=500
        )

        # Test 2: Complex aggregation
        await self.run_query_benchmark(
            "Complex Aggregation",
            """
            SELECT
                tenant_id,
                COUNT(*) as total_agents,
                COUNT(CASE WHEN status = 'active' THEN 1 END) as active_agents,
                MAX(created_at) as last_created
            FROM agents
            GROUP BY tenant_id
            """,
            iterations=500
        )

    async def benchmark_concurrent_load(self):
        """Benchmark concurrent query load"""
        print("\n=== Concurrent Load Benchmarks ===")

        # Test 1: Light concurrent load
        await self.run_concurrent_benchmark(
            "Concurrent Light Load (10 workers)",
            "SELECT * FROM agents LIMIT 10",
            concurrent_queries=10,
            iterations_per_worker=20
        )

        # Test 2: Medium concurrent load
        await self.run_concurrent_benchmark(
            "Concurrent Medium Load (50 workers)",
            "SELECT * FROM agents LIMIT 10",
            concurrent_queries=50,
            iterations_per_worker=20
        )

        # Test 3: Heavy concurrent load
        await self.run_concurrent_benchmark(
            "Concurrent Heavy Load (100 workers)",
            "SELECT * FROM agents LIMIT 10",
            concurrent_queries=100,
            iterations_per_worker=10
        )

    def print_summary(self):
        """Print benchmark summary"""
        print("\n" + "=" * 80)
        print("BENCHMARK SUMMARY")
        print("=" * 80)
        print(f"\nTotal Tests: {len(self.results)}")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("\n{:<45} {:>10} {:>10} {:>10}".format("Test Name", "Avg (ms)", "P95 (ms)", "QPS"))
        print("-" * 80)

        for result in self.results:
            print(f"{result.test_name:<45} {result.avg_time:>10.2f} {result.p95_time:>10.2f} {result.queries_per_second:>10.1f}")

        print("-" * 80)

        # Overall statistics
        all_avg_times = [r.avg_time for r in self.results]
        all_qps = [r.queries_per_second for r in self.results]

        print(f"\nOverall Average Response Time: {statistics.mean(all_avg_times):.2f}ms")
        print(f"Overall Average Throughput: {statistics.mean(all_qps):.1f} qps")
        print(f"Total Queries Executed: {sum(r.total_queries for r in self.results):,}")
        print(f"Total Errors: {sum(r.errors for r in self.results)}")

    def save_results(self, output_file: str):
        """Save results to JSON file"""
        data = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_tests": len(self.results),
                "total_queries": sum(r.total_queries for r in self.results),
                "total_errors": sum(r.errors for r in self.results),
                "overall_avg_time": statistics.mean([r.avg_time for r in self.results]),
                "overall_avg_qps": statistics.mean([r.queries_per_second for r in self.results]),
            },
            "results": [r.to_dict() for r in self.results]
        }

        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)

        print(f"\n✓ Results saved to: {output_file}")

    async def run_all_benchmarks(self):
        """Run all benchmark suites"""
        await self.setup()

        try:
            await self.benchmark_simple_queries()
            await self.benchmark_indexed_queries()
            await self.benchmark_joins()
            await self.benchmark_aggregations()
            await self.benchmark_concurrent_load()

            self.print_summary()

        finally:
            await self.cleanup()


async def main():
    parser = argparse.ArgumentParser(description='Database Performance Benchmark')
    parser.add_argument('--connection', default='postgresql://postgres:postgres@localhost:5434/agentic',
                        help='Database connection string')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    parser.add_argument('--output', default='tests/performance/reports/db-benchmark.json',
                        help='Output file for results')

    args = parser.parse_args()

    print("=" * 80)
    print("TempoNest Database Performance Benchmark")
    print("=" * 80)
    print(f"\nConnection: {args.connection.split('@')[1] if '@' in args.connection else args.connection}")
    print(f"Verbose: {args.verbose}")
    print(f"Output: {args.output}")

    benchmark = DatabaseBenchmark(args.connection, verbose=args.verbose)

    try:
        await benchmark.run_all_benchmarks()
        benchmark.save_results(args.output)
    except Exception as e:
        print(f"\n✗ Benchmark failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
