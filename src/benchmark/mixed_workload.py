import argparse
import csv
import random
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.db.client import CognoDBClient
from src.benchmark.metrics import calculate_latency_metrics


@dataclass
class Operation:
    operation_type: str
    parameters: dict[str, Any]


@dataclass
class OperationResult:
    operation_type: str
    latency_ms: float
    success: bool
    error: str | None = None


READ_QUERY = """
MATCH (n:User {id: $id})
RETURN n.id AS id
"""

WRITE_QUERY = """
MATCH (n:User {id: $id})
SET n.benchmark_value = $value
"""

CLEANUP_QUERY = """
MATCH (n:User)
REMOVE n.benchmark_value
"""


def load_node_ids(path: Path) -> list[int]:

    if not path.exists():
        raise FileNotFoundError(
            f"Nodes file not found: {path}"
        )

    node_ids = []

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:

        reader = csv.DictReader(file)

        if "id" not in (reader.fieldnames or []):
            raise ValueError(
                "nodes.csv must contain an 'id' column"
            )

        for row in reader:

            if row.get("id"):
                node_ids.append(
                    int(row["id"])
                )

    if not node_ids:
        raise ValueError(
            "No node IDs found"
        )

    return node_ids


def create_operations(
    node_ids: list[int],
    count: int,
    read_percentage: int,
    write_percentage: int,
    seed: int,
) -> list[Operation]:

    if read_percentage + write_percentage != 100:
        raise ValueError(
            "Read and write percentages must equal 100"
        )

    rng = random.Random(seed)

    read_count = (
        count * read_percentage // 100
    )

    write_count = count - read_count

    operations = []

    for _ in range(read_count):

        operations.append(
            Operation(
                operation_type="READ",
                parameters={
                    "id": rng.choice(node_ids)
                },
            )
        )

    for i in range(write_count):

        operations.append(
            Operation(
                operation_type="WRITE",
                parameters={
                    "id": rng.choice(node_ids),
                    "value": seed * 1_000_000 + i,
                },
            )
        )

    rng.shuffle(operations)

    return operations


def execute_operation(
    client: CognoDBClient,
    operation: Operation,
) -> OperationResult:

    start = time.perf_counter()

    try:

        if operation.operation_type == "READ":

            client.execute(
                READ_QUERY,
                operation.parameters,
            )

        else:

            client.execute_write(
                WRITE_QUERY,
                operation.parameters,
            )

        elapsed = (
            time.perf_counter() - start
        ) * 1000

        return OperationResult(
            operation_type=operation.operation_type,
            latency_ms=elapsed,
            success=True,
        )

    except Exception as exc:

        elapsed = (
            time.perf_counter() - start
        ) * 1000

        return OperationResult(
            operation_type=operation.operation_type,
            latency_ms=elapsed,
            success=False,
            error=str(exc),
        )


def run_workload(
    client: CognoDBClient,
    operations: list[Operation],
    concurrency: int,
):

    results = []

    start = time.perf_counter()

    with ThreadPoolExecutor(
        max_workers=concurrency
    ) as executor:

        futures = [
            executor.submit(
                execute_operation,
                client,
                operation,
            )
            for operation in operations
        ]

        for future in as_completed(futures):

            results.append(
                future.result()
            )

    elapsed = (
        time.perf_counter() - start
    )

    return results, elapsed


def cleanup(client: CognoDBClient) -> None:

    client.execute_write(
        CLEANUP_QUERY
    )


def calculate_metrics(
    results: list[OperationResult],
    elapsed: float,
) -> dict:

    successful = [
        r for r in results
        if r.success
    ]

    failed = [
        r for r in results
        if not r.success
    ]

    latencies = [
        r.latency_ms
        for r in successful
    ]

    metrics = {
        "total": len(results),
        "successful": len(successful),
        "failed": len(failed),
        "elapsed": elapsed,
        "qps": (
            len(successful) / elapsed
            if elapsed > 0
            else 0
        ),
    }

    if latencies:

        latency = calculate_latency_metrics(
            latencies
        )

        metrics["p50"] = latency["p50_ms"]
        metrics["p95"] = latency["p95_ms"]

    reads = [
        r.latency_ms
        for r in results
        if r.operation_type == "READ"
        and r.success
    ]

    writes = [
        r.latency_ms
        for r in results
        if r.operation_type == "WRITE"
        and r.success
    ]

    if reads:

        read_metrics = calculate_latency_metrics(
            reads
        )

        metrics["read_p50"] = (
            read_metrics["p50_ms"]
        )

        metrics["read_p95"] = (
            read_metrics["p95_ms"]
        )

    if writes:

        write_metrics = calculate_latency_metrics(
            writes
        )

        metrics["write_p50"] = (
            write_metrics["p50_ms"]
        )

        metrics["write_p95"] = (
            write_metrics["p95_ms"]
        )

    return metrics


def benchmark(
    client: CognoDBClient,
    node_ids: list[int],
    concurrency: int,
    warmup: int,
    iterations: int,
    read_percentage: int,
    write_percentage: int,
):

    print("\n" + "=" * 70)
    print(
        f"MIXED WORKLOAD - "
        f"CONCURRENCY {concurrency}"
    )
    print("=" * 70)

    # -------------------------------
    # WARMUP
    # -------------------------------

    warmup_operations = create_operations(
        node_ids=node_ids,
        count=warmup,
        read_percentage=read_percentage,
        write_percentage=write_percentage,
        seed=100 + concurrency,
    )

    print(
        f"Warm-up operations: {len(warmup_operations):,}"
    )

    run_workload(
        client,
        warmup_operations,
        concurrency,
    )

    cleanup(client)

    print("Warm-up complete.")

    # -------------------------------
    # MEASUREMENT
    # -------------------------------

    operations = create_operations(
        node_ids=node_ids,
        count=iterations,
        read_percentage=read_percentage,
        write_percentage=write_percentage,
        seed=1000 + concurrency,
    )

    read_count = sum(
        1
        for operation in operations
        if operation.operation_type == "READ"
    )

    write_count = sum(
        1
        for operation in operations
        if operation.operation_type == "WRITE"
    )

    print(
        f"Measurement operations: {len(operations):,}"
    )

    print(
        f"Reads:  {read_count:,}"
    )

    print(
        f"Writes: {write_count:,}"
    )

    results, elapsed = run_workload(
        client,
        operations,
        concurrency,
    )

    metrics = calculate_metrics(
        results,
        elapsed,
    )

    print("\nResults:")
    print(
        f"Total:       {metrics['total']:,}"
    )
    print(
        f"Successful:  {metrics['successful']:,}"
    )
    print(
        f"Failed:      {metrics['failed']:,}"
    )
    print(
        f"Elapsed:     {metrics['elapsed']:.3f} sec"
    )
    print(
        f"QPS:         {metrics['qps']:.2f}"
    )
    print(
        f"p50:         {metrics.get('p50', 0):.3f} ms"
    )
    print(
        f"p95:         {metrics.get('p95', 0):.3f} ms"
    )

    if "read_p50" in metrics:

        print(
            f"Read p50:    "
            f"{metrics['read_p50']:.3f} ms"
        )

        print(
            f"Read p95:    "
            f"{metrics['read_p95']:.3f} ms"
        )

    if "write_p50" in metrics:

        print(
            f"Write p50:   "
            f"{metrics['write_p50']:.3f} ms"
        )

        print(
            f"Write p95:   "
            f"{metrics['write_p95']:.3f} ms"
        )

    # Always clean up after measurement.
    cleanup(client)

    return metrics


def main() -> None:

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--nodes",
        default="data/benchmark/nodes.csv",
    )

    parser.add_argument(
        "--warmup",
        type=int,
        default=100,
    )

    parser.add_argument(
        "--iterations",
        type=int,
        default=1000,
    )

    parser.add_argument(
        "--read-percentage",
        type=int,
        default=70,
    )

    parser.add_argument(
        "--write-percentage",
        type=int,
        default=30,
    )

    parser.add_argument(
        "--concurrency",
        type=int,
        nargs="+",
        default=[1, 10, 40],
    )

    args = parser.parse_args()

    node_ids = load_node_ids(
        Path(args.nodes)
    )

    print("=" * 70)
    print("COGNODB MIXED WORKLOAD")
    print("=" * 70)

    print(
        f"Nodes:              {len(node_ids):,}"
    )

    print(
        f"Read percentage:    {args.read_percentage}%"
    )

    print(
        f"Write percentage:   {args.write_percentage}%"
    )

    print(
        f"Warm-up:             {args.warmup:,}"
    )

    print(
        f"Measurements:        {args.iterations:,}"
    )

    print(
        f"Concurrency:         {args.concurrency}"
    )

    all_results = {}

    # One shared driver/client.
    with CognoDBClient() as client:

        client.verify_connectivity()

        for concurrency in args.concurrency:

            all_results[concurrency] = benchmark(
                client=client,
                node_ids=node_ids,
                concurrency=concurrency,
                warmup=args.warmup,
                iterations=args.iterations,
                read_percentage=args.read_percentage,
                write_percentage=args.write_percentage,
            )

    print("\n" + "=" * 70)
    print("MIXED WORKLOAD SUMMARY")
    print("=" * 70)

    print(
        f"{'Concurrency':<15}"
        f"{'QPS':>12}"
        f"{'p50(ms)':>15}"
        f"{'p95(ms)':>15}"
        f"{'Errors':>10}"
    )

    print("-" * 70)

    for concurrency in args.concurrency:

        metrics = all_results[concurrency]

        print(
            f"{concurrency:<15}"
            f"{metrics['qps']:>12.2f}"
            f"{metrics.get('p50', 0):>15.3f}"
            f"{metrics.get('p95', 0):>15.3f}"
            f"{metrics['failed']:>10}"
        )


if __name__ == "__main__":
    main()