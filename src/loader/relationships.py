import argparse
import csv
import time
from pathlib import Path

from src.db.client import CognoDBClient


DEFAULT_BATCH_SIZE = 1_000


RELATIONSHIP_QUERY = """
UNWIND $rows AS row

MATCH (source:User {id: toInteger(row.source)})
MATCH (target:User {id: toInteger(row.target)})

CREATE (source)-[:FOLLOWS]->(target)
"""


def load_relationship_batch(
    client: CognoDBClient,
    rows: list[dict[str, str]],
) -> None:
    """
    Load one batch of FOLLOWS relationships.
    """

    if not rows:
        return

    client.execute_write(
        RELATIONSHIP_QUERY,
        {
            "rows": rows,
        },
    )


def load_relationships(
    client: CognoDBClient,
    input_path: Path,
    batch_size: int,
) -> tuple[int, float]:
    """
    Load all relationships from relationships.csv.

    Returns:
        total_relationships, elapsed_seconds
    """

    total_relationships = 0

    batch: list[dict[str, str]] = []

    start_time = time.perf_counter()

    with input_path.open(
        "r",
        encoding="utf-8",
    ) as file:

        reader = csv.DictReader(file)

        required_columns = {
            "source",
            "target",
        }

        actual_columns = set(
            reader.fieldnames or []
        )

        missing_columns = (
            required_columns - actual_columns
        )

        if missing_columns:
            raise ValueError(
                "relationships.csv is missing columns: "
                f"{sorted(missing_columns)}"
            )

        for row in reader:

            batch.append(row)

            if len(batch) >= batch_size:

                load_relationship_batch(
                    client,
                    batch,
                )

                total_relationships += len(batch)

                print(
                    f"Loaded relationships: "
                    f"{total_relationships:,}"
                )

                batch.clear()

        # Load remaining records.
        if batch:

            load_relationship_batch(
                client,
                batch,
            )

            total_relationships += len(batch)

            print(
                f"Loaded relationships: "
                f"{total_relationships:,}"
            )

    elapsed = (
        time.perf_counter()
        - start_time
    )

    return total_relationships, elapsed


def verify_relationship_count(
    client: CognoDBClient,
    expected_count: int,
) -> None:
    """
    Verify that CognoDB contains exactly the
    expected number of FOLLOWS relationships.
    """

    result = client.execute(
        """
        MATCH ()-[r:FOLLOWS]->()
        RETURN count(r) AS count
        """
    )

    actual_count = int(
        result[0]["count"]
    )

    print(
        f"Expected relationships: "
        f"{expected_count:,}"
    )

    print(
        f"Actual relationships:   "
        f"{actual_count:,}"
    )

    if actual_count != expected_count:
        raise RuntimeError(
            "Relationship count verification failed: "
            f"expected {expected_count:,}, "
            f"found {actual_count:,}"
        )


def main() -> None:

    parser = argparse.ArgumentParser(
        description=(
            "Load Pokec relationships into CognoDB."
        )
    )

    parser.add_argument(
        "--input",
        default=(
            "data/benchmark/"
            "relationships.csv"
        ),
    )

    parser.add_argument(
        "--batch-size",
        type=int,
        default=DEFAULT_BATCH_SIZE,
    )

    parser.add_argument(
        "--expected-count",
        type=int,
        default=100_000,
    )

    args = parser.parse_args()

    input_path = Path(
        args.input
    )

    if not input_path.exists():
        raise FileNotFoundError(
            "Relationship file not found: "
            f"{input_path}"
        )

    print("=" * 70)
    print("COGNODB RELATIONSHIP LOAD")
    print("=" * 70)

    print(
        f"Input:              {input_path}"
    )

    print(
        f"Batch size:         {args.batch_size:,}"
    )

    print(
        f"Expected count:     "
        f"{args.expected_count:,}"
    )

    with CognoDBClient() as client:

        client.verify_connectivity()

        count, elapsed = load_relationships(
            client=client,
            input_path=input_path,
            batch_size=args.batch_size,
        )

        verify_relationship_count(
            client=client,
            expected_count=args.expected_count,
        )

    throughput = (
        count / elapsed
        if elapsed > 0
        else 0
    )

    print("\n" + "=" * 70)
    print("RELATIONSHIP LOAD COMPLETE")
    print("=" * 70)

    print(
        f"Relationships loaded: "
        f"{count:,}"
    )

    print(
        f"Load time:            "
        f"{elapsed:.3f} seconds"
    )

    print(
        f"Throughput:           "
        f"{throughput:,.2f} relationships/sec"
    )


if __name__ == "__main__":
    main()