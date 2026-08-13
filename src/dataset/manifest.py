import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path


def count_csv_rows(path: Path) -> int:
    """
    Count data rows in a CSV file, excluding the header.
    """

    if not path.exists():
        raise FileNotFoundError(
            f"File not found: {path}"
        )

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:

        reader = csv.reader(file)

        # Skip header
        next(reader, None)

        return sum(
            1 for _ in reader
        )


def read_node_count(
    nodes_path: Path,
) -> int:

    return count_csv_rows(
        nodes_path
    )


def read_relationship_count(
    relationships_path: Path,
) -> int:

    return count_csv_rows(
        relationships_path
    )


def read_start_node_count(
    start_nodes_path: Path,
) -> int:

    return count_csv_rows(
        start_nodes_path
    )


def create_manifest(
    nodes_path: Path,
    relationships_path: Path,
    start_nodes_path: Path,
    output_path: Path,
    dataset_name: str,
    dataset_source: str,
    sampling_seed: int,
    start_node_seed: int,
) -> None:

    print("=" * 70)
    print("CREATING DATASET MANIFEST")
    print("=" * 70)

    node_count = read_node_count(
        nodes_path
    )

    relationship_count = (
        read_relationship_count(
            relationships_path
        )
    )

    start_node_count = (
        read_start_node_count(
            start_nodes_path
        )
    )

    manifest = {
        "dataset": {
            "name": dataset_name,
            "source": dataset_source,
        },
        "sampling": {
            "relationship_count": relationship_count,
            "seed": sampling_seed,
        },
        "benchmark": {
            "node_count": node_count,
            "relationship_count": relationship_count,
            "start_node_count": start_node_count,
            "start_node_seed": start_node_seed,
        },
        "files": {
            "nodes": str(nodes_path),
            "relationships": str(
                relationships_path
            ),
            "start_nodes": str(
                start_nodes_path
            ),
        },
        "generated_at_utc": (
            datetime.now(
                timezone.utc
            ).isoformat()
        ),
    }

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with output_path.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            manifest,
            file,
            indent=2,
        )

    print(
        f"Nodes:{node_count}"
    )

    print(
        f"Relationships:{relationship_count}"
    )

    print(
        f"Start nodes:{start_node_count}"
    )

    print(
        f"Sampling seed:{sampling_seed}"
    )

    print(
        f"Start node seed:{start_node_seed}"
    )

    print(
        f"Output:{output_path}"
    )

    print("\n" + "=" * 70)
    print("MANIFEST CREATED")
    print("=" * 70)


def main() -> None:

    parser = argparse.ArgumentParser(
        description=(
            "Create the SNAP soc-Pokec "
            "benchmark dataset manifest."
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
        "--relationships",
        default=(
            "data/benchmark/"
            "relationships.csv"
        ),
    )

    parser.add_argument(
        "--start-nodes",
        default=(
            "data/benchmark/"
            "start_nodes.csv"
        ),
    )

    parser.add_argument(
        "--output",
        default=(
            "data/benchmark/"
            "manifest.json"
        ),
    )

    parser.add_argument(
        "--dataset-name",
        default="SNAP soc-Pokec",
    )

    parser.add_argument(
        "--dataset-source",
        default=(
            "https://snap.stanford.edu/data/"
            "soc-Pokec.html"
        ),
    )

    parser.add_argument(
        "--sampling-seed",
        type=int,
        default=42,
    )

    parser.add_argument(
        "--start-node-seed",
        type=int,
        default=12345,
    )

    args = parser.parse_args()

    create_manifest(
        nodes_path=Path(args.nodes),
        relationships_path=Path(
            args.relationships
        ),
        start_nodes_path=Path(
            args.start_nodes
        ),
        output_path=Path(args.output),
        dataset_name=args.dataset_name,
        dataset_source=args.dataset_source,
        sampling_seed=args.sampling_seed,
        start_node_seed=args.start_node_seed,
    )


if __name__ == "__main__":
    main()