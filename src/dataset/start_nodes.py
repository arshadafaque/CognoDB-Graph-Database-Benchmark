import argparse
import csv
import random
from pathlib import Path


def load_source_node_ids(
    relationships_path: Path,
) -> list[int]:
    """
    Load unique source node IDs from relationships.csv.

    A source node is guaranteed to have at least one
    outgoing relationship in the benchmark dataset.
    """

    if not relationships_path.exists():
        raise FileNotFoundError(
            f"Relationships file not found: "
            f"{relationships_path}"
        )

    source_nodes: set[int] = set()

    with relationships_path.open(
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

            source = row.get("source")

            if not source:
                continue

            source_nodes.add(
                int(source)
            )

    return sorted(source_nodes)


def select_start_nodes(
    source_nodes: list[int],
    count: int,
    seed: int,
) -> list[int]:
    """
    Randomly select start nodes from nodes that have
    at least one outgoing relationship.
    """

    if count <= 0:
        raise ValueError(
            "Start node count must be greater than zero."
        )

    if count > len(source_nodes):
        raise ValueError(
            f"Requested {count:,} start nodes, "
            f"but only {len(source_nodes):,} "
            f"unique source nodes are available."
        )

    rng = random.Random(seed)

    selected = rng.sample(
        source_nodes,
        count,
    )

    selected.sort()

    return selected


def write_start_nodes(
    start_nodes: list[int],
    output_path: Path,
) -> None:
    """
    Write start nodes to CSV.
    """

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with output_path.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:

        writer = csv.writer(file)

        writer.writerow(
            ["id"]
        )

        for node_id in start_nodes:
            writer.writerow(
                [node_id]
            )


def create_start_nodes(
    relationships_path: Path,
    output_path: Path,
    count: int,
    seed: int,
) -> None:

    print("=" * 70)
    print("GENERATING TRAVERSAL START NODES")
    print("=" * 70)

    print(
        f"Relationships: {relationships_path}"
    )

    print(
        f"Requested:     {count:,}"
    )

    print(
        f"Seed:          {seed}"
    )

    source_nodes = load_source_node_ids(
        relationships_path
    )

    print(
        f"Unique source nodes: "
        f"{len(source_nodes):,}"
    )

    start_nodes = select_start_nodes(
        source_nodes=source_nodes,
        count=count,
        seed=seed,
    )

    write_start_nodes(
        start_nodes=start_nodes,
        output_path=output_path,
    )

    print("\n" + "=" * 70)
    print("START NODE GENERATION COMPLETE")
    print("=" * 70)

    print(
        f"Start nodes: {len(start_nodes):,}"
    )

    print(
        f"Seed:        {seed}"
    )

    print(
        f"Output:      {output_path}"
    )


def main() -> None:

    parser = argparse.ArgumentParser(
        description=(
            "Generate deterministic traversal "
            "start nodes from relationship sources."
        )
    )

    parser.add_argument(
        "--relationships",
        default=(
            "data/benchmark/"
            "relationships.csv"
        ),
    )

    parser.add_argument(
        "--output",
        default=(
            "data/benchmark/"
            "start_nodes.csv"
        ),
    )

    parser.add_argument(
        "--count",
        type=int,
        default=100,
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=12345,
    )

    args = parser.parse_args()

    create_start_nodes(
        relationships_path=Path(
            args.relationships
        ),
        output_path=Path(
            args.output
        ),
        count=args.count,
        seed=args.seed,
    )


if __name__ == "__main__":
    main()