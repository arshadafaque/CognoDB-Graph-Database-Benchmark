from neo4j import GraphDatabase
from dotenv import load_dotenv
import os

load_dotenv()

URI=os.getenv("COGNODB_URI")
USERNAME=os.getenv("COGNODB_USERNAME")
PASSWORD=os.getenv("COGNODB_PASSWORD")


def main():
    print("Connecting to CognoDB...")

    with GraphDatabase.driver(
        URI,
        auth=(USERNAME, PASSWORD),
    ) as driver:

        driver.verify_connectivity()

        print("Connection successful!")


if __name__ == "__main__":
    main()