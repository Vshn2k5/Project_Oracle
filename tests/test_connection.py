from src.knowledge_graph.connection import create_neo4j_connection


def main() -> None:
    connection = create_neo4j_connection()

    try:
        with connection.session() as session:
            result = session.run("RETURN 1 AS test")
            record = result.single()

            if record is None:
                raise RuntimeError("Neo4j returned no result.")

            print("Session test successful.")
            print("Result from Neo4j:", record["test"])

    finally:
        connection.close()


if __name__ == "__main__":
    main()