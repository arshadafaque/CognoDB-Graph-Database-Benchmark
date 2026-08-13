import csv
from pathlib import Path

from src.db.client import CognoDBClient


def load_start_nodes() -> list[int]:

    path = Path(
        "data/benchmark/start_nodes.csv"
    )

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:

        reader = csv.DictReader(file)

        return [
            int(row["id"])
            for row in reader
            if row.get("id")
        ]


def main() -> None:

    start_nodes = load_start_nodes()

    print(
        f"Checking {len(start_nodes)} start nodes..."
    )

    with CognoDBClient() as client:

        client.verify_connectivity()

        zero_outgoing = 0

        total_outgoing = 0

        for start_id in start_nodes:

            result = client.execute(
                """
                MATCH (start:User {id: $start_id})
                      -[:FOLLOWS]->(target)
                RETURN count(target) AS count
                """,
                {
                    "start_id": start_id
                },
            )

            count = int(
                result[0]["count"]
            )

            total_outgoing += count

            if count == 0:
                zero_outgoing += 1

        print(
            f"Total outgoing edges: "
            f"{total_outgoing:,}"
        )

        print(
            f"Start nodes with zero outgoing edges: "
            f"{zero_outgoing}"
        )

        if zero_outgoing != 0:
            raise RuntimeError(
                "Some start nodes have no outgoing "
                "FOLLOWS relationships."
            )

    print(
        "All start nodes have at least one "
        "outgoing relationship."
    )


if __name__ == "__main__":
    main()