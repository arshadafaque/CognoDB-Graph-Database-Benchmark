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


POINT_LOOKUP_QUERY = """
MATCH (n:User {id: $id})
RETURN n.id AS id
"""


FILTERED_LOOKUP_QUERY = """
MATCH (n:User)
WHERE n.age = $age
RETURN count(n) AS count
"""


def load_benchmark_values(
    nodes_path: Path,
) -> tuple[list[int], list[int]]:
    """
    Load node IDs and valid ages from nodes.csv.

    IDs are used for point lookups.
    Ages are used for filtered lookups.
    """

    if not nodes_path.exists():
        raise FileNotFoundError(
            f"Nodes file not found: {nodes_path}"
        )

    node_ids: list[int] = []
    ages: list[int] = []

    with nodes_path.open(
        "r",
        encoding="utf-8",
    ) as file:

        reader = csv.DictReader(file)

        required_columns = {
            "id",
            "age",
        }

        actual_columns = set(
            reader.fieldnames or []
        )

        missing_columns = (
            required_columns - actual_columns
        )

        if missing_columns:
            raise ValueError(
                "nodes.csv is missing columns: "
                f"{sorted(missing_columns)}"
            )

        for row in reader:

            raw_id = row.get("id")

            if raw_id:
                node_ids.append(
                    int(raw_id)
                )

            raw_age = row.get("age")

            if raw_age:
                try:
                    age = int(raw_age)
                except ValueError:
                    continue

                ages.append(age)

    if not node_ids:
        raise ValueError(
            "No node IDs found."
        )

    if not ages:
        raise ValueError(
            "No valid ages found."
        )

    return node_ids, ages


def run_query(
    client: CognoDBClient,
    query: str,
    parameters: dict,
) -> None:

    client.execute(
        query,
        parameters,
    )


def warmup_point_lookup(
    client: CognoDBClient,
    node_ids: list[int],
    iterations: int,
) -> None:

    for i in range(iterations):

        node_id = node_ids[
            i % len(node_ids)
        ]

        run_query(
            client,
            POINT_LOOKUP_QUERY,
            {
                "id": node_id
            },
        )


def measure_point_lookup(
    client: CognoDBClient,
    node_ids: list[int],
    iterations: int,
) -> list[float]:

    latencies_ms: list[float] = []

    for i in range(iterations):

        node_id = node_ids[
            i % len(node_ids)
        ]

        start = time.perf_counter()

        run_query(
            client,
            POINT_LOOKUP_QUERY,
            {
                "id": node_id
            },
        )

        elapsed = (
            time.perf_counter()
            - start
        )

        latencies_ms.append(
            elapsed * 1000
        )

    return latencies_ms


def warmup_filtered_lookup(
    client: CognoDBClient,
    ages: list[int],
    iterations: int,
) -> None:

    for i in range(iterations):

        age = ages[
            i % len(ages)
        ]

        run_query(
            client,
            FILTERED_LOOKUP_QUERY,
            {
                "age": age
            },
        )


def measure_filtered_lookup(
    client: CognoDBClient,
    ages: list[int],
    iterations: int,
) -> list[float]:

    latencies_ms: list[float] = []

    for i in range(iterations):

        age = ages[
            i % len(ages)
        ]

        start = time.perf_counter()

        run_query(
            client,
            FILTERED_LOOKUP_QUERY,
            {
                "age": age
            },
        )

        elapsed = (
            time.perf_counter()
            - start
        )

        latencies_ms.append(
            elapsed * 1000
        )

    return latencies_ms


def main() -> None:

    parser = argparse.ArgumentParser(
        description=(
            "Benchmark point and filtered "
            "lookups in CognoDB."
        )
    )

    parser.add_argument(
        "--nodes",
        default=(
            "data/benchmark/"
            "nodes.csv"
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

    nodes_path = Path(
        args.nodes
    )

    node_ids, ages = load_benchmark_values(
        nodes_path
    )

    print("=" * 70)
    print("COGNODB LOOKUP BENCHMARK")
    print("=" * 70)

    print(
        f"Available node IDs: {len(node_ids):,}"
    )

    print(
        f"Available age values: {len(ages):,}"
    )

    print(
        f"Warm-up iterations: {args.warmup}"
    )

    print(
        f"Measurement iterations: "
        f"{args.iterations}"
    )

    with CognoDBClient() as client:

        client.verify_connectivity()

        # --------------------------------------------------
        # POINT LOOKUP
        # --------------------------------------------------

        print("\n" + "=" * 70)
        print("POINT LOOKUP")
        print("=" * 70)

        print("Warming up...")

        warmup_point_lookup(
            client,
            node_ids,
            args.warmup,
        )

        print("Warm-up complete.")

        print("Running measurements...")

        point_latencies = (
            measure_point_lookup(
                client,
                node_ids,
                args.iterations,
            )
        )

        point_metrics = (
            calculate_latency_metrics(
                point_latencies
            )
        )

        print_latency_metrics(
            "POINT LOOKUP",
            point_metrics,
        )

        # --------------------------------------------------
        # FILTERED LOOKUP
        # --------------------------------------------------

        print("\n" + "=" * 70)
        print("FILTERED LOOKUP")
        print("=" * 70)

        print(
            "Indexed property: User.age"
        )

        print("Warming up...")

        warmup_filtered_lookup(
            client,
            ages,
            args.warmup,
        )

        print("Warm-up complete.")

        print("Running measurements...")

        filtered_latencies = (
            measure_filtered_lookup(
                client,
                ages,
                args.iterations,
            )
        )

        filtered_metrics = (
            calculate_latency_metrics(
                filtered_latencies
            )
        )

        print_latency_metrics(
            "FILTERED LOOKUP",
            filtered_metrics,
        )

    # ------------------------------------------------------
    # SUMMARY
    # ------------------------------------------------------

    print("\n" + "=" * 70)
    print("LOOKUP BENCHMARK SUMMARY")
    print("=" * 70)

    print(
        f"{'Workload':<20}"
        f"{'p50 (ms)':>15}"
        f"{'p95 (ms)':>15}"
    )

    print("-" * 50)

    print(
        f"{'Point lookup':<20}"
        f"{point_metrics['p50_ms']:>15.3f}"
        f"{point_metrics['p95_ms']:>15.3f}"
    )

    print(
        f"{'Filtered lookup':<20}"
        f"{filtered_metrics['p50_ms']:>15.3f}"
        f"{filtered_metrics['p95_ms']:>15.3f}"
    )


if __name__ == "__main__":
    main()