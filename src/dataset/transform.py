import argparse
import csv
import gzip
from pathlib import Path


# These are the first 8 columns of the Pokec profile file.
PROFILE_COLUMNS = [
    "id",
    "public",
    "completion_percentage",
    "gender",
    "region",
    "last_login",
    "registration",
    "age",
]


def load_relationships(
    relationships_path: Path,
) -> tuple[list[tuple[int, int]], set[int]]:
    """
    Read sampled relationships and collect all unique user IDs.
    """

    relationships: list[tuple[int, int]] = []
    node_ids: set[int] = set()

    print("=" * 70)
    print("LOADING RELATIONSHIPS")
    print("=" * 70)
    print(f"Input: {relationships_path}")

    if not relationships_path.exists():
        raise FileNotFoundError(
            f"Relationships file not found: {relationships_path}"
        )

    with relationships_path.open(
        "r",
        encoding="utf-8",
    ) as file:

        reader = csv.DictReader(file)

        for row in reader:

            source = int(row["source"])
            target = int(row["target"])

            relationships.append(
                (source, target)
            )

            node_ids.add(source)
            node_ids.add(target)

    print(
        f"Relationships loaded: {len(relationships):,}"
    )

    print(
        f"Unique users found: {len(node_ids):,}"
    )

    return relationships, node_ids


def load_profiles_for_nodes(
    profiles_path: Path,
    required_node_ids: set[int],
) -> dict[int, dict]:
    """
    Read the Pokec profile file and keep profiles only for
    users that appear in our sampled relationship dataset.

    The complete Pokec profile file is much larger than the
    benchmark subset, so we don't load the entire file into memory.
    """

    profiles: dict[int, dict] = {}

    print("\n" + "=" * 70)
    print("LOADING PROFILE DATA")
    print("=" * 70)
    print(f"Input: {profiles_path}")

    if not profiles_path.exists():
        raise FileNotFoundError(
            f"Profiles file not found: {profiles_path}"
        )

    scanned_rows = 0

    with gzip.open(
        profiles_path,
        "rt",
        encoding="utf-8",
        errors="replace",
    ) as file:

        for line in file:

            line = line.rstrip("\n\r")

            if not line:
                continue

            if line.startswith("#"):
                continue

            parts = line.split("\t")

            if len(parts) < 8:
                continue

            try:
                user_id = int(parts[0])
            except ValueError:
                continue

            scanned_rows += 1

            # We only care about users that occur in our
            # sampled relationship dataset.
            if user_id not in required_node_ids:
                continue

            profiles[user_id] = {
                "id": user_id,
                "public": normalize_integer(
                    parts[1]
                ),
                "completion_percentage": normalize_integer(
                    parts[2]
                ),
                "gender": normalize_integer(
                    parts[3]
                ),
                "region": normalize_string(
                    parts[4]
                ),
                "last_login": normalize_string(
                    parts[5]
                ),
                "registration": normalize_string(
                    parts[6]
                ),
                "age": normalize_integer(
                    parts[7]
                ),
            }

            # Once we have every required profile,
            # there is no reason to continue scanning.
            if len(profiles) == len(required_node_ids):
                break

    missing_profiles = (
        required_node_ids - profiles.keys()
    )

    print(
        f"Profile rows scanned: {scanned_rows:,}"
    )

    print(
        f"Matching profiles:    {len(profiles):,}"
    )

    print(
        f"Missing profiles:     {len(missing_profiles):,}"
    )

    if missing_profiles:
        print(
            "\nWARNING: Some relationship users do not "
            "have profile records."
        )

        preview = sorted(
            missing_profiles
        )[:20]

        print(
            f"First missing IDs: {preview}"
        )

    return profiles


def normalize_integer(
    value: str,
) -> int | None:
    """
    Convert a Pokec numeric value to int.

    Pokec uses 'null' for missing values.
    """

    value = value.strip()

    if not value or value.lower() == "null":
        return None

    try:
        return int(value)
    except ValueError:
        return None


def normalize_string(
    value: str,
) -> str | None:
    """
    Convert Pokec string values.

    'null' is represented as None.
    """

    value = value.strip()

    if not value or value.lower() == "null":
        return None

    return value


def write_relationships(
    relationships: list[tuple[int, int]],
    output_path: Path,
) -> None:
    """
    Write normalized benchmark relationships.
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
            [
                "source",
                "target",
            ]
        )

        for source, target in relationships:

            writer.writerow(
                [
                    source,
                    target,
                ]
            )

    print("\n" + "=" * 70)
    print("RELATIONSHIP TRANSFORMATION COMPLETE")
    print("=" * 70)

    print(
        f"Relationships: {len(relationships):,}"
    )

    print(
        f"Output:        {output_path}"
    )


def write_nodes(
    node_ids: set[int],
    profiles: dict[int, dict],
    output_path: Path,
) -> None:
    """
    Write benchmark nodes with selected Pokec profile properties.

    We write every node that participates in the sampled
    relationships. If a profile is missing, the profile
    properties are written as empty values.
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
            [
                "id",
                "public",
                "completion_percentage",
                "gender",
                "region",
                "last_login",
                "registration",
                "age",
            ]
        )

        for node_id in sorted(node_ids):

            profile = profiles.get(
                node_id,
                {},
            )

            writer.writerow(
                [
                    node_id,
                    profile.get("public"),
                    profile.get(
                        "completion_percentage"
                    ),
                    profile.get("gender"),
                    profile.get("region"),
                    profile.get("last_login"),
                    profile.get("registration"),
                    profile.get("age"),
                ]
            )

    print("\n" + "=" * 70)
    print("NODE TRANSFORMATION COMPLETE")
    print("=" * 70)

    print(
        f"Nodes:   {len(node_ids):,}"
    )

    print(
        f"Output:  {output_path}"
    )


def main() -> None:

    parser = argparse.ArgumentParser(
        description=(
            "Transform sampled SNAP soc-Pokec "
            "data into benchmark CSV files."
        )
    )

    parser.add_argument(
        "--relationships",
        default=(
            "data/benchmark/"
            "relationships_sampled.csv"
        ),
    )

    parser.add_argument(
        "--profiles",
        default=(
            "data/raw/snap_pokec/"
            "soc-pokec-profiles.txt.gz"
        ),
    )

    parser.add_argument(
        "--output-relationships",
        default=(
            "data/benchmark/"
            "relationships.csv"
        ),
    )

    parser.add_argument(
        "--output-nodes",
        default=(
            "data/benchmark/"
            "nodes.csv"
        ),
    )

    args = parser.parse_args()

    relationships_path = Path(
        args.relationships
    )

    profiles_path = Path(
        args.profiles
    )

    relationships_output_path = Path(
        args.output_relationships
    )

    nodes_output_path = Path(
        args.output_nodes
    )

    # ---------------------------------------------------------
    # 1. Read sampled relationships
    # ---------------------------------------------------------

    relationships, node_ids = (
        load_relationships(
            relationships_path
        )
    )

    # ---------------------------------------------------------
    # 2. Read matching profile records
    # ---------------------------------------------------------

    profiles = load_profiles_for_nodes(
        profiles_path,
        node_ids,
    )

    # ---------------------------------------------------------
    # 3. Write relationships.csv
    # ---------------------------------------------------------

    write_relationships(
        relationships,
        relationships_output_path,
    )

    # ---------------------------------------------------------
    # 4. Write nodes.csv
    # ---------------------------------------------------------

    write_nodes(
        node_ids,
        profiles,
        nodes_output_path,
    )

    print("\n" + "=" * 70)
    print("TRANSFORMATION COMPLETE")
    print("=" * 70)

    print(
        f"Final nodes:         {len(node_ids):,}"
    )

    print(
        f"Final relationships: {len(relationships):,}"
    )

    print(
        f"Profiles found:      {len(profiles):,}"
    )

    print(
        f"Profiles missing:    "
        f"{len(node_ids) - len(profiles):,}"
    )


if __name__ == "__main__":
    main()