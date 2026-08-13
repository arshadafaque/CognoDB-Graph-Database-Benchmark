from src.db.client import CognoDBClient


def main() -> None:

    print("=" * 70)
    print("CLEANING BENCHMARK RELATIONSHIPS")
    print("=" * 70)

    with CognoDBClient() as client:

        client.verify_connectivity()

        print(
            "Deleting BENCHMARK_WRITE relationships..."
        )

        client.execute_write(
            """
            MATCH ()-[r:BENCHMARK_WRITE]->()
            DELETE r
            """
        )

        result = client.execute(
            """
            MATCH ()-[r:BENCHMARK_WRITE]->()
            RETURN count(r) AS count
            """
        )

        remaining = int(
            result[0]["count"]
        )

        print(
            f"Remaining BENCHMARK_WRITE "
            f"relationships: {remaining:,}"
        )

        if remaining != 0:
            raise RuntimeError(
                "Benchmark cleanup failed."
            )

    print("=" * 70)
    print("BENCHMARK CLEANUP COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()