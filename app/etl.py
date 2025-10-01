from neo4j import GraphDatabase

uri = "bolt://neo4j_db:7687"  # service name in docker-compose
driver = GraphDatabase.driver(uri, auth=("neo4j", "test"))

def create_node(tx, name):
    tx.run("CREATE (n:Person {name: $name})", name=name)

with driver.session() as session:
    session.execute_write(create_node, "Alice")
