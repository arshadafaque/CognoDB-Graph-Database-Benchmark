from src.db.client import CognoDBClient


def main() -> None:

    print("=" * 70)
    print("COGNODB RESOURCE / FOOTPRINT METRICS")
    print("=" * 70)

    with CognoDBClient() as client:

        client.verify_connectivity()

        # ---------------------------------------------
        # NODE COUNT
        # ---------------------------------------------

        nodes = client.execute(
            """
            MATCH (n)
            RETURN count(n) AS count
            """
        )

        node_count = int(
            nodes[0]["count"]
        )

        # ---------------------------------------------
        # RELATIONSHIP COUNT
        # ---------------------------------------------

        relationships = client.execute(
            """
            MATCH ()-[r]->()
            RETURN count(r) AS count
            """
        )

        relationship_count = int(
            relationships[0]["count"]
        )

        # ---------------------------------------------
        # RELATIONSHIP TYPES
        # ---------------------------------------------

        relationship_types = client.execute(
            """
            MATCH ()-[r]->()
            RETURN type(r) AS type,
                   count(r) AS count
            ORDER BY count DESC
            """
        )

    print()
    print(
        f"Nodes:           {node_count:,}"
    )

    print(
        f"Relationships:   {relationship_count:,}"
    )

    print()
    print("Relationship types:")

    for record in relationship_types:

        print(
            f"  {record['type']}: "
            f"{record['count']:,}"
        )

    print()
    print("Platform resources:")
    print("  Storage:        See CognoDB Console")
    print("  Memory:         See CognoDB Console")
    print("  CPU:            Not observable from driver")
    print("  Instance size:  See CognoDB Console")
    print("  Region:         See CognoDB Console")
    print("  Connections:    See CognoDB Console")

    print()
    print("=" * 70)
    print("RESOURCE METRICS COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()