import argparse
import csv
import time
from pathlib import Path

from src.db.client import CognoDBClient


DEFAULT_BATCH_SIZE = 1_000


NODE_QUERY = """
UNWIND $rows AS row

CREATE (n:User {
    id: toInteger(row.id),

    public: CASE
        WHEN row.public IS NULL OR row.public = ''
        THEN NULL
        ELSE toInteger(row.public)
    END,

    completion_percentage: CASE
        WHEN row.completion_percentage IS NULL
             OR row.completion_percentage = ''
        THEN NULL
        ELSE toInteger(row.completion_percentage)
    END,

    gender: CASE
        WHEN row.gender IS NULL OR row.gender = ''
        THEN NULL
        ELSE toInteger(row.gender)
    END,

    region: CASE
        WHEN row.region IS NULL OR row.region = ''
        THEN NULL
        ELSE row.region
    END,

    last_login: CASE
        WHEN row.last_login IS NULL OR row.last_login = ''
        THEN NULL
        ELSE row.last_login
    END,

    registration: CASE
        WHEN row.registration IS NULL OR row.registration = ''
        THEN NULL
        ELSE row.registration
    END,

    age: CASE
        WHEN row.age IS NULL OR row.age = ''
        THEN NULL
        ELSE toInteger(row.age)
    END
})
"""


def load_node_batch(
    client: CognoDBClient,
    rows: list[dict[str, str]],
) -> None:
    """
    Load one batch of User nodes.
    """

    if not rows:
        return

    client.execute_write(
        NODE_QUERY,
        {
            "rows": rows,
        },
    )


def load_nodes(
    client: CognoDBClient,
    input_path: Path,
    batch_size: int,
) -> tuple[int, float]:
    """
    Load all nodes from nodes.csv.

    Returns:
        total_nodes, elapsed_seconds
    """

    total_nodes = 0

    batch: list[dict[str, str]] = []

    start_time = time.perf_counter()

    with input_path.open(
        "r",
        encoding="utf-8",
    ) as file:

        reader = csv.DictReader(file)

        required_columns = {
            "id",
            "public",
            "completion_percentage",
            "gender",
            "region",
            "last_login",
            "registration",
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

            batch.append(row)

            if len(batch) >= batch_size:

                load_node_batch(
                    client,
                    batch,
                )

                total_nodes += len(batch)

                print(
                    f"Loaded nodes: "
                    f"{total_nodes:,}"
                )

                batch.clear()

        # Load remaining records.
        if batch:

            load_node_batch(
                client,
                batch,
            )

            total_nodes += len(batch)

            print(
                f"Loaded nodes: "
                f"{total_nodes:,}"
            )

    elapsed = (
        time.perf_counter()
        - start_time
    )

    return total_nodes, elapsed


def verify_node_count(
    client: CognoDBClient,
    expected_count: int,
) -> None:
    """
    Verify that the database contains exactly the
    number of nodes that were loaded.
    """

    result = client.execute(
        """
        MATCH (n:User)
        RETURN count(n) AS count
        """
    )

    actual_count = int(
        result[0]["count"]
    )

    print(
        f"Expected nodes: {expected_count:,}"
    )

    print(
        f"Actual nodes:   {actual_count:,}"
    )

    if actual_count != expected_count:
        raise RuntimeError(
            "Node count verification failed: "
            f"expected {expected_count:,}, "
            f"found {actual_count:,}"
        )


def main() -> None:

    parser = argparse.ArgumentParser(
        description=(
            "Load Pokec User nodes into CognoDB."
        )
    )

    parser.add_argument(
        "--input",
        default=(
            "data/benchmark/"
            "nodes.csv"
        ),
    )

    parser.add_argument(
        "--batch-size",
        type=int,
        default=DEFAULT_BATCH_SIZE,
    )

    args = parser.parse_args()

    input_path = Path(
        args.input
    )

    if not input_path.exists():
        raise FileNotFoundError(
            f"Node file not found: {input_path}"
        )

    print("=" * 70)
    print("COGNODB NODE LOAD")
    print("=" * 70)

    print(
        f"Input:      {input_path}"
    )

    print(
        f"Batch size: {args.batch_size:,}"
    )

    with CognoDBClient() as client:

        client.verify_connectivity()

        count, elapsed = load_nodes(
            client=client,
            input_path=input_path,
            batch_size=args.batch_size,
        )

        verify_node_count(
            client=client,
            expected_count=count,
        )

    throughput = (
        count / elapsed
        if elapsed > 0
        else 0
    )

    print("\n" + "=" * 70)
    print("NODE LOAD COMPLETE")
    print("=" * 70)

    print(
        f"Nodes loaded: {count:,}"
    )

    print(
        f"Load time:    {elapsed:.3f} seconds"
    )

    print(
        f"Throughput:   {throughput:,.2f} nodes/sec"
    )


if __name__ == "__main__":
    main()