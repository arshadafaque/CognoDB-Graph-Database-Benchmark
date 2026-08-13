import argparse
import csv
import time
from pathlib import Path

from src.db.client import CognoDBClient
from src.benchmark.metrics import (
    calculate_latency_metrics,
    print_latency_metrics,
)


DEFAULT_WARMUP_ITERATIONS = 20
DEFAULT_MEASUREMENT_ITERATIONS = 100


TRAVERSAL_QUERIES = {
    1: """
        MATCH (start:User {id: $start_id})
              -[:FOLLOWS*1]->(target)
        RETURN count(target) AS count
    """,

    2: """
        MATCH (start:User {id: $start_id})
              -[:FOLLOWS*2]->(target)
        RETURN count(target) AS count
    """,

    3: """
        MATCH (start:User {id: $start_id})
              -[:FOLLOWS*3]->(target)
        RETURN count(target) AS count
    """,
}


def load_start_nodes(
    path: Path,
) -> list[int]:
    """
    Load the fixed benchmark start nodes.
    """

    if not path.exists():
        raise FileNotFoundError(
            f"Start-node file not found: {path}"
        )

    start_nodes: list[int] = []

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:

        reader = csv.DictReader(file)

        if "id" not in (
            reader.fieldnames or []
        ):
            raise ValueError(
                "start_nodes.csv must contain "
                "an 'id' column."
            )

        for row in reader:

            raw_id = row.get("id")

            if raw_id:
                start_nodes.append(
                    int(raw_id)
                )

    if not start_nodes:
        raise ValueError(
            "No start nodes found."
        )

    return start_nodes


def run_query(
    client: CognoDBClient,
    query: str,
    start_id: int,
) -> None:
    """
    Execute one traversal query.

    We intentionally don't include query-result
    processing in the latency measurement.
    """

    client.execute(
        query,
        {
            "start_id": start_id,
        },
    )


def warmup(
    client: CognoDBClient,
    query: str,
    start_nodes: list[int],
    iterations: int,
) -> None:
    """
    Warm up the database before measurement.
    """

    for i in range(iterations):

        start_id = start_nodes[
            i % len(start_nodes)
        ]

        run_query(
            client,
            query,
            start_id,
        )


def measure(
    client: CognoDBClient,
    query: str,
    start_nodes: list[int],
    iterations: int,
) -> list[float]:
    """
    Measure query latency in milliseconds.
    """

    latencies_ms: list[float] = []

    for i in range(iterations):

        start_id = start_nodes[
            i % len(start_nodes)
        ]

        start_time = time.perf_counter()

        run_query(
            client,
            query,
            start_id,
        )

        elapsed = (
            time.perf_counter()
            - start_time
        )

        latency_ms = (
            elapsed * 1000
        )

        latencies_ms.append(
            latency_ms
        )

    return latencies_ms


def benchmark_depth(
    client: CognoDBClient,
    depth: int,
    start_nodes: list[int],
    warmup_iterations: int,
    measurement_iterations: int,
) -> dict[str, float]:

    query = TRAVERSAL_QUERIES[
        depth
    ]

    print("\n" + "=" * 70)
    print(
        f"TRAVERSAL DEPTH: {depth}-HOP"
    )
    print("=" * 70)

    print(
        f"Warm-up iterations: "
        f"{warmup_iterations}"
    )

    print(
        f"Measurement iterations: "
        f"{measurement_iterations}"
    )

    print(
        f"Start nodes: "
        f"{len(start_nodes)}"
    )

    print("Warming up...")

    warmup(
        client=client,
        query=query,
        start_nodes=start_nodes,
        iterations=warmup_iterations,
    )

    print("Warm-up complete.")

    print("Running measurements...")

    latencies = measure(
        client=client,
        query=query,
        start_nodes=start_nodes,
        iterations=measurement_iterations,
    )

    metrics = calculate_latency_metrics(
        latencies
    )

    print_latency_metrics(
        name=f"{depth}-HOP TRAVERSAL",
        metrics=metrics,
    )

    return metrics


def main() -> None:

    parser = argparse.ArgumentParser(
        description=(
            "Benchmark 1-hop, 2-hop and 3-hop "
            "traversals in CognoDB."
        )
    )

    parser.add_argument(
        "--start-nodes",
        default=(
            "data/benchmark/"
            "start_nodes.csv"
        ),
    )

    parser.add_argument(
        "--warmup",
        type=int,
        default=DEFAULT_WARMUP_ITERATIONS,
    )

    parser.add_argument(
        "--iterations",
        type=int,
        default=DEFAULT_MEASUREMENT_ITERATIONS,
    )

    args = parser.parse_args()

    start_nodes = load_start_nodes(
        Path(args.start_nodes)
    )

    print("=" * 70)
    print("COGNODB TRAVERSAL BENCHMARK")
    print("=" * 70)

    print(
        f"Start nodes: "
        f"{len(start_nodes):,}"
    )

    print(
        f"Warm-up: "
        f"{args.warmup:,}"
    )

    print(
        f"Measurements: "
        f"{args.iterations:,}"
    )

    with CognoDBClient() as client:

        client.verify_connectivity()

        all_metrics = {}

        for depth in (1, 2, 3):

            all_metrics[depth] = (
                benchmark_depth(
                    client=client,
                    depth=depth,
                    start_nodes=start_nodes,
                    warmup_iterations=args.warmup,
                    measurement_iterations=args.iterations,
                )
            )

    print("\n" + "=" * 70)
    print("TRAVERSAL BENCHMARK SUMMARY")
    print("=" * 70)

    print(
        f"{'Depth':<10}"
        f"{'p50 (ms)':>15}"
        f"{'p95 (ms)':>15}"
    )

    print("-" * 40)

    for depth, metrics in all_metrics.items():

        print(
            f"{depth}-hop"
            f"{metrics['p50_ms']:>15.3f}"
            f"{metrics['p95_ms']:>15.3f}"
        )


if __name__ == "__main__":
    main()