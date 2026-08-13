import argparse
import time

from src.db.client import CognoDBClient
from src.benchmark.metrics import (
    calculate_latency_metrics,
    print_latency_metrics,
)


DEFAULT_WARMUP_ITERATIONS = 20
DEFAULT_MEASUREMENT_ITERATIONS = 100


AGGREGATION_QUERY = """
MATCH (n:User)
WHERE n.age IS NOT NULL
RETURN n.age AS age, count(n) AS user_count
ORDER BY n.age
"""


def run_query(
    client: CognoDBClient,
) -> None:

    client.execute(
        AGGREGATION_QUERY
    )


def warmup(
    client: CognoDBClient,
    iterations: int,
) -> None:

    for _ in range(iterations):
        run_query(client)


def measure(
    client: CognoDBClient,
    iterations: int,
) -> list[float]:

    latencies_ms: list[float] = []

    for _ in range(iterations):

        start = time.perf_counter()

        run_query(client)

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
            "Benchmark aggregation queries "
            "in CognoDB."
        )
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

    print("=" * 70)
    print("COGNODB AGGREGATION BENCHMARK")
    print("=" * 70)

    print(
        f"Warm-up iterations: "
        f"{args.warmup}"
    )

    print(
        f"Measurement iterations: "
        f"{args.iterations}"
    )

    with CognoDBClient() as client:

        client.verify_connectivity()

        print("\nWarming up...")

        warmup(
            client,
            args.warmup,
        )

        print("Warm-up complete.")

        print(
            "Running measurements..."
        )

        latencies = measure(
            client,
            args.iterations,
        )

        metrics = (
            calculate_latency_metrics(
                latencies
            )
        )

    print_latency_metrics(
        "AGE GROUP-BY AGGREGATION",
        metrics,
    )

    print("\n" + "=" * 70)
    print("AGGREGATION BENCHMARK SUMMARY")
    print("=" * 70)

    print(
        f"p50:  "
        f"{metrics['p50_ms']:.3f} ms"
    )

    print(
        f"p95:  "
        f"{metrics['p95_ms']:.3f} ms"
    )


if __name__ == "__main__":
    main()