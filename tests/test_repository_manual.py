from src.knowledge_graph.repository import create_repository


def main() -> None:
    with create_repository() as repository:
        risk = repository.upsert_risk(
            node_id="RISK-TEST-001",
            risk_type="urban_flood",
            severity="high",
            description="Temporary relationship verification risk.",
        )

        infrastructure = repository.upsert_infrastructure(
            node_id="INF-TEST-001",
            name="Test Hospital",
            infrastructure_type="hospital",
            description="Temporary relationship verification infrastructure.",
        )

        relationship = repository.link_risk_to_infrastructure(
            risk_id=risk.node_id,
            infrastructure_id=infrastructure.node_id,
        )

        print("Risk:", risk.node_id)
        print("Infrastructure:", infrastructure.node_id)
        print("Relationship:", relationship.relationship_type)


if __name__ == "__main__":
    main()