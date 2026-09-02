import os

from dotenv import load_dotenv
from neo4j import Driver, GraphDatabase


# Load environment variables from .env
load_dotenv()


NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "neo4j")


def validate_configuration() -> None:
    """Ensure all required Neo4j configuration values are available."""
    required = {
        "NEO4J_URI": NEO4J_URI,
        "NEO4J_USERNAME": NEO4J_USERNAME,
        "NEO4J_PASSWORD": NEO4J_PASSWORD,
        "NEO4J_DATABASE": NEO4J_DATABASE,
    }

    missing = [key for key, value in required.items() if not value]

    if missing:
        raise RuntimeError(
            f"Missing Neo4j configuration: {', '.join(missing)}"
        )


def create_driver() -> Driver:
    """Create and verify the Neo4j database driver."""
    validate_configuration()

    driver = GraphDatabase.driver(
        NEO4J_URI,
        auth=(NEO4J_USERNAME, NEO4J_PASSWORD),
    )

    driver.verify_connectivity()

    return driver


def create_project_node(driver: Driver, project_name: str) -> dict:
    """Create the Project node if it does not already exist."""

    query = """
    MERGE (p:Project {name: $name})
    RETURN
        elementId(p) AS id,
        p.name AS name
    """

    with driver.session(database=NEO4J_DATABASE) as session:
        record = session.execute_write(
            lambda tx: tx.run(query, name=project_name).single()
        )

    if record is None:
        raise RuntimeError("Neo4j did not return the created Project node.")

    return dict(record)


def main() -> None:
    """Application entry point."""

    driver = create_driver()

    try:
        project = create_project_node(
            driver,
            project_name="Project Oracle",
        )

        print("Neo4j connection successful.")
        print(f"Project node: {project['name']}")
        print(f"Node ID: {project['id']}")

    finally:
        driver.close()


if __name__ == "__main__":
    main()