import argparse
import gzip
from pathlib import Path


def inspect_relationships(
    path: Path,
    sample_size: int = 100_000,
) -> None:
    """
    Inspect the Pokec relationship file without loading
    the entire 30M+ edge dataset into memory.
    """

    print("=" * 70)
    print("RELATIONSHIP FILE")
    print("=" * 70)
    print(f"Path: {path}")

    if not path.exists():
        raise FileNotFoundError(
            f"File not found: {path}"
        )

    edge_count = 0
    first_edges = []
    unique_nodes = set()

    with gzip.open(
        path,
        "rt",
        encoding="utf-8",
        errors="replace",
    ) as file:

        for line in file:

            line = line.strip()

            if not line:
                continue

            if line.startswith("#"):
                continue

            parts = line.split()

            if len(parts) < 2:
                continue

            source = parts[0]
            target = parts[1]

            edge_count += 1

            if len(first_edges) < 10:
                first_edges.append(
                    (source, target)
                )

            if len(unique_nodes) < sample_size:
                unique_nodes.add(source)
                unique_nodes.add(target)

    print(
        f"Relationship count: {edge_count:,}"
    )

    print(
        f"Unique nodes observed in sample: "
        f"{len(unique_nodes):,}"
    )

    print("\nFirst 10 relationships:")

    for source, target in first_edges:
        print(
            f"  {source} -> {target}"
        )


def inspect_profiles(
    path: Path,
    sample_size: int = 10,
) -> None:
    """
    Inspect the Pokec profile file.

    We intentionally inspect the raw structure first
    because we don't want to assume the profile columns.
    """

    print("\n" + "=" * 70)
    print("PROFILE FILE")
    print("=" * 70)
    print(f"Path: {path}")

    if not path.exists():
        raise FileNotFoundError(
            f"File not found: {path}"
        )

    rows = 0

    with gzip.open(
        path,
        "rt",
        encoding="utf-8",
        errors="replace",
    ) as file:

        for line in file:

            line = line.rstrip("\n")

            if not line:
                continue

            if line.startswith("#"):
                print(
                    f"Header/comment: {line[:300]}"
                )
                continue

            parts = line.split()

            print(
                f"Columns: {len(parts)}"
            )

            print(
                f"Values: {parts[:30]}"
            )

            rows += 1

            if rows >= sample_size:
                break


def main() -> None:

    parser = argparse.ArgumentParser(
        description=(
            "Inspect the SNAP soc-Pokec dataset."
        )
    )

    parser.add_argument(
        "--relationships",
        default=(
            "data/raw/snap_pokec/"
            "soc-pokec-relationships.txt.gz"
        ),
    )

    parser.add_argument(
        "--profiles",
        default=(
            "data/raw/snap_pokec/"
            "soc-pokec-profiles.txt.gz"
        ),
    )

    args = parser.parse_args()

    inspect_relationships(
        Path(args.relationships)
    )

    inspect_profiles(
        Path(args.profiles)
    )


if __name__ == "__main__":
    main()