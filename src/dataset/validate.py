import argparse
import csv
from pathlib import Path


EXPECTED_RELATIONSHIPS = 250_000


def load_nodes(nodes_path: Path) -> tuple[set[int], dict]:
    """
    Load nodes.csv and validate the expected node properties.

    Returns:
        node_ids: Set of all node IDs.
        stats: Node validation statistics.
    """

    nodes: set[int] = set()

    duplicate_node_count = 0
    missing_id_count = 0

    rows_with_age = 0
    rows_with_gender = 0
    rows_with_region = 0

    expected_columns = {
        "id",
        "public",
        "completion_percentage",
        "gender",
        "region",
        "last_login",
        "registration",
        "age",
    }

    print("=" * 70)
    print("VALIDATING NODES")
    print("=" * 70)

    if not nodes_path.exists():
        raise FileNotFoundError(
            f"Nodes file not found: {nodes_path}"
        )

    with nodes_path.open(
        "r",
        encoding="utf-8",
    ) as file:

        reader = csv.DictReader(file)

        if reader.fieldnames is None:
            raise ValueError(
                "nodes.csv does not contain a header."
            )

        actual_columns = set(
            reader.fieldnames
        )

        missing_columns = (
            expected_columns - actual_columns
        )

        if missing_columns:
            raise ValueError(
                "nodes.csv is missing expected "
                f"columns: {sorted(missing_columns)}"
            )

        for row in reader:

            raw_id = row.get("id")

            if not raw_id:
                missing_id_count += 1
                continue

            node_id = int(raw_id)

            if node_id in nodes:
                duplicate_node_count += 1

            nodes.add(node_id)

            if row.get("age"):
                rows_with_age += 1

            if row.get("gender"):
                rows_with_gender += 1

            if row.get("region"):
                rows_with_region += 1

    print(
        f"Unique nodes:              {len(nodes):,}"
    )

    print(
        f"Duplicate node records:    "
        f"{duplicate_node_count:,}"
    )

    print(
        f"Missing node IDs:           "
        f"{missing_id_count:,}"
    )

    print(
        f"Nodes with age:             "
        f"{rows_with_age:,}"
    )

    print(
        f"Nodes with gender:          "
        f"{rows_with_gender:,}"
    )

    print(
        f"Nodes with region:          "
        f"{rows_with_region:,}"
    )

    return nodes, {
        "node_count": len(nodes),
        "duplicate_nodes": duplicate_node_count,
        "missing_node_ids": missing_id_count,
        "nodes_with_age": rows_with_age,
        "nodes_with_gender": rows_with_gender,
        "nodes_with_region": rows_with_region,
    }


def validate_relationships(
    relationships_path: Path,
    nodes: set[int],
) -> dict:
    """
    Validate relationships.csv.

    Checks:
    - relationship count
    - duplicate relationships
    - source node existence
    - target node existence
    """

    relationship_count = 0
    duplicate_count = 0
    invalid_reference_count = 0

    seen_edges: set[tuple[int, int]] = set()

    print("\n" + "=" * 70)
    print("VALIDATING RELATIONSHIPS")
    print("=" * 70)

    if not relationships_path.exists():
        raise FileNotFoundError(
            f"Relationships file not found: "
            f"{relationships_path}"
        )

    with relationships_path.open(
        "r",
        encoding="utf-8",
    ) as file:

        reader = csv.DictReader(file)

        required_columns = {
            "source",
            "target",
        }

        if reader.fieldnames is None:
            raise ValueError(
                "relationships.csv does not contain "
                "a header."
            )

        actual_columns = set(
            reader.fieldnames
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

            source = int(row["source"])
            target = int(row["target"])

            relationship_count += 1

            edge = (
                source,
                target,
            )

            if edge in seen_edges:
                duplicate_count += 1
            else:
                seen_edges.add(edge)

            if source not in nodes:
                invalid_reference_count += 1

            if target not in nodes:
                invalid_reference_count += 1

    print(
        f"Relationships:           "
        f"{relationship_count:,}"
    )

    print(
        f"Duplicate relationships: "
        f"{duplicate_count:,}"
    )

    print(
        f"Invalid node references:  "
        f"{invalid_reference_count:,}"
    )

    return {
        "relationship_count": relationship_count,
        "duplicate_relationships": duplicate_count,
        "invalid_references": invalid_reference_count,
    }


def validate_dataset(
    nodes_path: Path,
    relationships_path: Path,
    expected_relationships: int,
) -> None:
    """
    Run all dataset validation checks.
    """

    nodes, node_stats = load_nodes(
        nodes_path
    )

    relationship_stats = validate_relationships(
        relationships_path,
        nodes,
    )

    errors: list[str] = []

    # ---------------------------------------------------------
    # Node validation
    # ---------------------------------------------------------

    if node_stats["node_count"] == 0:
        errors.append(
            "nodes.csv contains no nodes."
        )

    if node_stats["duplicate_nodes"] > 0:
        errors.append(
            "Duplicate node records were found."
        )

    if node_stats["missing_node_ids"] > 0:
        errors.append(
            "Some node records have missing IDs."
        )

    # ---------------------------------------------------------
    # Relationship validation
    # ---------------------------------------------------------

    actual_relationships = (
        relationship_stats["relationship_count"]
    )

    if actual_relationships != expected_relationships:
        errors.append(
            f"Expected {expected_relationships:,} "
            f"relationships, but found "
            f"{actual_relationships:,}."
        )

    if relationship_stats[
        "invalid_references"
    ] > 0:
        errors.append(
            "Some relationships reference nodes "
            "that do not exist in nodes.csv."
        )

    # Duplicate relationships are reported but are
    # not automatically treated as an error.
    #
    # This is intentional because removing duplicates
    # would change the sampled benchmark dataset.

    # ---------------------------------------------------------
    # Final result
    # ---------------------------------------------------------

    print("\n" + "=" * 70)
    print("DATASET VALIDATION SUMMARY")
    print("=" * 70)

    print(
        f"Nodes:                     "
        f"{node_stats['node_count']:,}"
    )

    print(
        f"Relationships:             "
        f"{relationship_stats['relationship_count']:,}"
    )

    print(
        f"Duplicate nodes:           "
        f"{node_stats['duplicate_nodes']:,}"
    )

    print(
        f"Duplicate relationships:   "
        f"{relationship_stats['duplicate_relationships']:,}"
    )

    print(
        f"Invalid references:        "
        f"{relationship_stats['invalid_references']:,}"
    )

    print(
        f"Nodes with age:            "
        f"{node_stats['nodes_with_age']:,}"
    )

    print(
        f"Nodes with gender:         "
        f"{node_stats['nodes_with_gender']:,}"
    )

    print(
        f"Nodes with region:         "
        f"{node_stats['nodes_with_region']:,}"
    )

    if errors:

        print("\n" + "=" * 70)
        print("VALIDATION FAILED")
        print("=" * 70)

        for error in errors:
            print(f"ERROR: {error}")

        raise SystemExit(1)

    print("\n" + "=" * 70)
    print("VALIDATION PASSED")
    print("=" * 70)


def main() -> None:

    parser = argparse.ArgumentParser(
        description=(
            "Validate the SNAP soc-Pokec "
            "benchmark dataset."
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
        "--expected-relationships",
        type=int,
        default=EXPECTED_RELATIONSHIPS,
    )

    args = parser.parse_args()

    validate_dataset(
        nodes_path=Path(args.nodes),
        relationships_path=Path(
            args.relationships
        ),
        expected_relationships=(
            args.expected_relationships
        ),
    )


if __name__ == "__main__":
    main()