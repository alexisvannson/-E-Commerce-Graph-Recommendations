from neo4j import GraphDatabase
import time
from pathlib import Path
import psycopg2
import os
from typing import List, Any, Dict, Tuple


# Configuration - can be overridden by environment variables
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "yourStrongPassword123")
NEO4J_AUTH = (NEO4J_USER, NEO4J_PASSWORD)
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "postgres")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
POSTGRES_DB = os.getenv("POSTGRES_DB", "shop")
POSTGRES_USER = os.getenv("POSTGRES_USER", "myuser")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "mypassword")
BATCH_SIZE = 1000

# Global driver (initialized after Neo4j is ready)
driver = None


def wait_for_postgres(host=None, port=None, db_name=None, 
                     user=None, password=None):
    """Wait for PostgreSQL to be ready by attempting connections."""
    host = host or POSTGRES_HOST
    port = port or POSTGRES_PORT
    db_name = db_name or POSTGRES_DB
    user = user or POSTGRES_USER
    password = password or POSTGRES_PASSWORD
    
    print("Waiting for PostgreSQL to be ready...")
    while True:
        try:
            conn = psycopg2.connect(
                database=db_name,
                user=user,
                password=password,
                host=host,
                port=port,
                connect_timeout=2
            )
            conn.close()
            print("PostgreSQL is ready.")
            return True
        except psycopg2.OperationalError:
            print("PostgreSQL is not ready yet, waiting...")
            time.sleep(2)
        except Exception as e:
            raise Exception(f"PostgreSQL connection error: {e}")


def wait_for_neo4j(uri=None, auth=None):
    """Wait for Neo4j to be ready by attempting driver connection."""
    global driver
    uri = uri or NEO4J_URI
    auth = auth or NEO4J_AUTH
    
    print("Waiting for Neo4j to be ready...")
    test_driver = None
    while True:
        try:
            test_driver = GraphDatabase.driver(uri, auth=auth)
            test_driver.verify_connectivity()
            # Initialize global driver once Neo4j is ready
            driver = test_driver
            print("Neo4j is ready.")
            return True
        except Exception as e:
            if test_driver:
                test_driver.close()
            error_msg = str(e).lower()
            if "authentication" in error_msg or "unauthorized" in error_msg:
                raise Exception(f"Neo4j authentication error: {e}")
            print(f"Neo4j is not ready yet, waiting... ({e})")
            time.sleep(2)


def run_cypher(query: str, parameters: Dict[str, Any] = None) -> Any:
    """Executes a single Cypher query."""
    if driver is None:
        raise Exception("Neo4j driver is not initialized. Call wait_for_neo4j() first.")
    
    with driver.session() as session:
        if parameters:
            result = session.run(query, parameters)
        else:
            result = session.run(query)
        return result.values()


def run_cypher_file(file_path: str) -> None:
    """Executes multiple Cypher statements from a file."""
    if driver is None:
        raise Exception("Neo4j driver is not initialized. Call wait_for_neo4j() first.")
    
    queries_path = Path(file_path)
    if not queries_path.exists():
        raise FileNotFoundError(f"Cypher file not found: {file_path}")
    
    with open(queries_path, "r") as file:
        queries_content = file.read()
    
    # Split queries by semicolon and filter out empty lines and comments
    queries = [
        q.strip() 
        for q in queries_content.split(';') 
        if q.strip() and not q.strip().startswith('//')
    ]
    
    with driver.session() as session:
        for query in queries:
            if query:  # Double check it's not empty
                session.run(query)
    print(f"Executed {len(queries)} Cypher statements from {file_path}")


def chunk(data: List[Any], chunk_size: int = BATCH_SIZE) -> List[List[Any]]:
    """Splits a list into chunks of specified size for batch processing."""
    return [data[i:i + chunk_size] for i in range(0, len(data), chunk_size)]


def extract_data_from_postgres(database=None, user=None, 
                               password=None, host=None, 
                               port=None) -> Dict[str, List[Tuple]]:
    """Extract data from PostgreSQL database."""
    database = database or POSTGRES_DB
    user = user or POSTGRES_USER
    password = password or POSTGRES_PASSWORD
    host = host or POSTGRES_HOST
    port = port or POSTGRES_PORT
    
    conn = psycopg2.connect(
        database=database,
        user=user,
        password=password,
        host=host,
        port=port
    )
    cursor = conn.cursor()

    tables = {}
    
    # Extract customers
    cursor.execute("SELECT id, name, join_date FROM customers;")
    tables['customers'] = cursor.fetchall()

    # Extract categories
    cursor.execute("SELECT id, name FROM categories;")
    tables['categories'] = cursor.fetchall()

    # Extract products
    cursor.execute("SELECT id, name, price, category_id FROM products;")
    tables['products'] = cursor.fetchall()

    # Extract orders
    cursor.execute("SELECT id, customer_id, ts FROM orders;")
    tables['orders'] = cursor.fetchall()

    # Extract order_items
    cursor.execute("SELECT order_id, product_id, quantity FROM order_items;")
    tables['order_items'] = cursor.fetchall()

    # Extract events
    cursor.execute("SELECT id, customer_id, product_id, event_type, ts FROM events;")
    tables['events'] = cursor.fetchall()

    cursor.close()
    conn.close()
    return tables


def transform_data_to_neo4j(tables: Dict[str, List[Tuple]]) -> Tuple[List[Dict], List[Dict]]:
    """Transform PostgreSQL data into Neo4j node and relationship structures."""
    nodes = []
    relationships = []

    # Customers -> Nodes
    for row in tables['customers']:
        nodes.append({
            "label": "Customer",
            "props": {"id": row[0], "name": row[1], "joinDate": str(row[2])}
        })

    # Categories -> Nodes
    for row in tables['categories']:
        nodes.append({
            "label": "Category",
            "props": {"id": row[0], "name": row[1]}
        })

    # Products -> Nodes + Relationships to Category
    for row in tables['products']:
        nodes.append({
            "label": "Product",
            "props": {"id": row[0], "name": row[1], "price": float(row[2])}
        })
        if row[3]:  # category_id exists
            relationships.append({
                "start_label": "Product",
                "start_key": "id",
                "start_value": row[0],
                "end_label": "Category",
                "end_key": "id",
                "end_value": row[3],
                "rel_type": "BELONGS_TO"
            })

    # Orders -> Nodes + Relationships to Customer
    for row in tables['orders']:
        nodes.append({
            "label": "Order",
            "props": {"id": row[0], "timestamp": str(row[2])}
        })
        relationships.append({
            "start_label": "Customer",
            "start_key": "id",
            "start_value": row[1],
            "end_label": "Order",
            "end_key": "id",
            "end_value": row[0],
            "rel_type": "PLACED"
        })

    # Order Items -> Relationships
    for row in tables['order_items']:
        relationships.append({
            "start_label": "Order",
            "start_key": "id",
            "start_value": row[0],
            "end_label": "Product",
            "end_key": "id",
            "end_value": row[1],
            "rel_type": "CONTAINS",
            "props": {"quantity": row[2]}
        })

    # Events -> Nodes + Relationships
    for row in tables['events']:
        nodes.append({
            "label": "Event",
            "props": {
                "id": row[0],
                "eventType": row[3],
                "timestamp": str(row[4])
            }
        })
        relationships.append({
            "start_label": "Customer",
            "start_key": "id",
            "start_value": row[1],
            "end_label": "Event",
            "end_key": "id",
            "end_value": row[0],
            "rel_type": "DID"
        })
        relationships.append({
            "start_label": "Event",
            "start_key": "id",
            "start_value": row[0],
            "end_label": "Product",
            "end_key": "id",
            "end_value": row[2],
            "rel_type": "ON"
        })

    return nodes, relationships


def load_data_to_neo4j(nodes: List[Dict], relationships: List[Dict]) -> None:
    """Load nodes and relationships into Neo4j database."""
    if driver is None:
        raise Exception("Neo4j driver is not initialized. Call wait_for_neo4j() first.")
    
    def _create_nodes(tx, batch):
        for item in batch:
            label = item["label"]
            # Use MERGE for idempotency - will create if doesn't exist, update if exists
            # Assuming 'id' is the unique identifier for all node types
            id_prop = item["props"].get("id")
            if id_prop:
                # Use MERGE with id property for idempotent operations
                # Remove id from props dict since it's used in MERGE
                props_dict = {k: v for k, v in item["props"].items() if k != "id"}
                # Build SET clause for updating properties
                if props_dict:
                    props_set = ", ".join([f"n.{k} = ${k}" for k in props_dict.keys()])
                    query = f"MERGE (n:{label} {{id: $id}}) SET {props_set}"
                    params = {"id": id_prop, **props_dict}
                else:
                    query = f"MERGE (n:{label} {{id: $id}})"
                    params = {"id": id_prop}
                tx.run(query, params)
            else:
                # Fallback to CREATE if no id property
                props = ", ".join([f"{k}: ${k}" for k in item["props"].keys()])
                query = f"CREATE (:{label} {{ {props} }})"
                tx.run(query, **item["props"])

    def _create_relationships(tx, batch):
        for rel in batch:
            props = rel.get("props", {})
            if props:
                # Use SET with individual property assignments
                props_set = ", ".join([f"r.{k} = ${k}" for k in props.keys()])
                query = f"""
                MATCH (a:{rel['start_label']} {{{rel['start_key']}: $start_val}})
                MATCH (b:{rel['end_label']} {{{rel['end_key']}: $end_val}})
                MERGE (a)-[r:{rel['rel_type']}]->(b)
                SET {props_set}
                """
                params = {"start_val": rel["start_value"], "end_val": rel["end_value"], **props}
            else:
                query = f"""
                MATCH (a:{rel['start_label']} {{{rel['start_key']}: $start_val}})
                MATCH (b:{rel['end_label']} {{{rel['end_key']}: $end_val}})
                MERGE (a)-[:{rel['rel_type']}]->(b)
                """
                params = {"start_val": rel["start_value"], "end_val": rel["end_value"]}
            tx.run(query, **params)

    with driver.session() as session:
        # Process nodes in batches
        node_batches = chunk(nodes, BATCH_SIZE)
        for batch in node_batches:
            session.execute_write(_create_nodes, batch)
        print(f"Created {len(nodes)} nodes in {len(node_batches)} batch(es)")

        # Process relationships in batches
        rel_batches = chunk(relationships, BATCH_SIZE)
        for batch in rel_batches:
            session.execute_write(_create_relationships, batch)
        print(f"Created {len(relationships)} relationships in {len(rel_batches)} batch(es)")


def etl() -> bool:
    """Main ETL function: Extract, Transform, and Load data from PostgreSQL to Neo4j."""
    try:
        # Wait for databases to be ready
        wait_for_postgres()
        wait_for_neo4j()
        
        # Create Neo4j schema
        queries_path = Path(__file__).with_name("queries.cypher")
        run_cypher_file(str(queries_path))
        print("Neo4j schema created successfully.")

        # Extract data from PostgreSQL
        raw_data = extract_data_from_postgres()
        print("Data extracted from PostgreSQL successfully.")

        # Transform data to Neo4j format
        nodes, relationships = transform_data_to_neo4j(raw_data)
        print(f"Data transformed into Neo4j format successfully: {len(nodes)} nodes, {len(relationships)} relationships")

        # Load data into Neo4j
        load_data_to_neo4j(nodes, relationships)
        print("Data loaded into Neo4j successfully.")
        
        print("ETL process completed successfully.")
        return True
        
    except Exception as e:
        print(f"ETL process failed: {e}")
        raise
    finally:
        # Close driver connection
        if driver:
            driver.close()
            print("Neo4j driver closed.")


if __name__ == "__main__":
    etl()
