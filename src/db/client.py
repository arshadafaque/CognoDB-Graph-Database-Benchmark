import os
from typing import Any

from dotenv import load_dotenv
from neo4j import Driver, GraphDatabase


load_dotenv()


class CognoDBClient:
    """
    Client for connecting to CognoDB using the official Neo4j driver.
    """

    def __init__(self) -> None:
        uri = os.getenv("COGNODB_URI")
        username = os.getenv("COGNODB_USERNAME")
        password = os.getenv("COGNODB_PASSWORD")

        if not uri:
            raise ValueError(
                "COGNODB_URI is not set in .env"
            )

        if not username:
            raise ValueError(
                "COGNODB_USERNAME is not set in .env"
            )

        if not password:
            raise ValueError(
                "COGNODB_PASSWORD is not set in .env"
            )

        self.driver: Driver = GraphDatabase.driver(
            uri,
            auth=(username, password),
        )

    def verify_connectivity(self) -> None:
        """Verify connectivity and authentication."""
        self.driver.verify_connectivity()

    def execute(
        self,
        query: str,
        parameters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Execute a read/query and return records.
        """

        with self.driver.session() as session:
            result = session.run(
                query,
                parameters or {},
            )

            return result.data()

    def execute_write(
        self,
        query: str,
        parameters: dict[str, Any] | None = None,
    ) -> None:
        """
        Execute a write query.

        Important:
        We consume the result instead of iterating over records.
        This avoids trying to deserialize unexpected records returned
        by the CognoDB server for CREATE/WRITE statements.
        """

        with self.driver.session() as session:

            def transaction_work(tx) -> None:
                result = tx.run(
                    query,
                    parameters or {},
                )

                # Force the database to finish the query/transaction.
                result.consume()

            session.execute_write(
                transaction_work
            )

    def close(self) -> None:
        """Close the Neo4j driver."""
        self.driver.close()

    def __enter__(self):
        return self

    def __exit__(
        self,
        exc_type,
        exc_value,
        traceback,
    ) -> None:
        self.close()