from src.db.client import CognoDBClient


def create_schema(
    client: CognoDBClient,
) -> None:
    """
    Create the schema required for the benchmark.
    """

    print("=" * 70)
    print("CREATING COGNODB SCHEMA")
    print("=" * 70)

    # Unique constraint on User.id.
    #
    # This also provides an index for point lookups
    # and for finding source/target nodes while loading
    # relationships.
    print("Creating User.id uniqueness constraint...")

    client.execute_write(
        """
        CREATE CONSTRAINT user_id_unique IF NOT EXISTS
        FOR (n:User)
        REQUIRE n.id IS UNIQUE
        """
    )

    print("User.id constraint created.")

    # Index for filtered lookups and aggregations.
    print("Creating User.age index...")

    client.execute_write(
        """
        CREATE INDEX user_age_index IF NOT EXISTS
        FOR (n:User)
        ON (n.age)
        """
    )

    print("User.age index created.")

    print("=" * 70)
    print("SCHEMA CREATION COMPLETE")
    print("=" * 70)


def main() -> None:

    with CognoDBClient() as client:

        client.verify_connectivity()

        create_schema(client)


if __name__ == "__main__":
    main()