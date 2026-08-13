from src.db.client import CognoDBClient


def main() -> None:

    print("=" * 70)
    print("CLEANING COGNODB")
    print("=" * 70)

    with CognoDBClient() as client:

        client.verify_connectivity()

        print("Deleting existing User graph...")

        client.execute_write(
            """
            MATCH (n:User)
            DETACH DELETE n
            """
        )

        result = client.execute(
            """
            MATCH (n:User)
            RETURN count(n) AS count
            """
        )

        remaining = result[0]["count"]

        print(
            f"Remaining User nodes: {remaining:,}"
        )

        if remaining != 0:
            raise RuntimeError(
                "Cleanup failed. User nodes still exist."
            )

    print("=" * 70)
    print("CLEANUP COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()