from src.db.client import CognoDBClient


def main() -> None:

    print("=" * 70)
    print("COGNODB SCHEMA SETUP")
    print("=" * 70)

    with CognoDBClient() as client:

        client.verify_connectivity()

        # --------------------------------------------------
        # User ID constraint
        # --------------------------------------------------

        print("Creating User.id constraint...")

        client.execute(
            """
            CREATE CONSTRAINT user_id_unique
            IF NOT EXISTS
            FOR (n:User)
            REQUIRE n.id IS UNIQUE
            """
        )

        print("User.id constraint ready.")

        # --------------------------------------------------
        # Age index
        # --------------------------------------------------

        print("Creating User.age index...")

        client.execute(
            """
            CREATE INDEX user_age_index
            IF NOT EXISTS
            FOR (n:User)
            ON (n.age)
            """
        )

        print("User.age index ready.")

        # --------------------------------------------------
        # Verify schema
        # --------------------------------------------------

        print("\nVerifying indexes and constraints...")

        indexes = client.execute(
            """
            SHOW INDEXES
            """
        )

        print("\nIndexes:")

        for record in indexes:

            print(
                record
            )

        constraints = client.execute(
            """
            SHOW CONSTRAINTS
            """
        )

        print("\nConstraints:")

        for record in constraints:

            print(
                record
            )

    print("=" * 70)
    print("SCHEMA SETUP COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()