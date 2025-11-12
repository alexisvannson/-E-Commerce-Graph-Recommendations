# E-Commerce Graph Recommendations

A comprehensive ETL pipeline that extracts e-commerce data from PostgreSQL, transforms it into a graph structure, and loads it into Neo4j for advanced recommendation system capabilities.


##  Overview

This project demonstrates a modern data pipeline architecture that:
- **Extracts** transactional e-commerce data from PostgreSQL
- **Transforms** relational data into graph structures optimized for recommendations
- **Loads** data into Neo4j for graph-based analytics and recommendations

The system includes a FastAPI service for health monitoring and a comprehensive ETL process with helper utilities for batch processing and Cypher query execution.

##  Architecture

The system consists of four main services:

1. **PostgreSQL** - Relational database storing e-commerce transactions
2. **Neo4j** - Graph database for relationship-based recommendations
3. **FastAPI App** - REST API service with health endpoints
4. **Checks Service** - Automated end-to-end testing and validation


## Recommendation Strategies

**Graph-Based Techniques**
- Personalized PageRank on the `Customer` → `Product` graph to surface similar items with strong interaction paths.
- Community detection (e.g., Louvain, Label Propagation) to cluster customers or products into affinity groups.
- Shortest-path and k-nearest-neighbor traversals to combine purchase, event, and category relationships.

**Hybrid Approaches**
- Blend collaborative filtering with graph features by exporting embeddings (GraphSAGE, node2vec) for use in downstream ML models.
- Incorporate content attributes (category, price bucket, brand) to cold-start recommendations for new products.
- Use event-weighted scoring to capture intent (e.g., `view` < `add_to_cart` < `purchase`).

**Operational Best Practices**
- Schedule offline batch jobs for heavy graph analytics and persist scored recommendation lists in PostgreSQL or a cache.
- Expose real-time lookups through parameterized Cypher or FastAPI endpoints that accept customer or basket context.
- Run A/B experiments comparing recommendation pipelines and track business KPIs (CTR, conversion rate, average order value).

##  Scaling Options

**Data Volume & Throughput**
- Tune Neo4j with appropriate page cache and heap sizes; monitor `neo4j` container memory usage and adjust Docker resources.
- Partition ETL loads into smaller batches (`chunk_size`) and enable APOC `periodic.iterate` for large upserts.
- Introduce Kafka or a message queue to capture streaming events, emitting incremental updates instead of full reloads.

**Service Architecture**
- Deploy PostgreSQL and Neo4j on managed services or separate hosts to prevent CPU contention from analytics workloads.
- Front the FastAPI service with a load balancer and enable connection pooling (e.g., `asyncpg`, `uvicorn --workers`) for concurrency.
- Leverage Redis or another cache for hot recommendation results, invalidating on significant data changes.

**Reliability & Observability**
- Add metrics exporters (Prometheus, Neo4j metrics) and dashboards to visualize query latency and graph size growth.
- Automate backups and point-in-time recovery for PostgreSQL and Neo4j volumes.
- Define infrastructure-as-code (Terraform, Ansible) to reproduce environments and scale clusters consistently.


##  Quick Start

### 1. Clone the Repository

```bash
git clone <repository-url>
cd -E-Commerce-Graph-Recommendations
```

### 2. Start All Services

```bash
docker compose up -d
```

This will start:
- PostgreSQL on port `5432`
- Neo4j Browser on port `7474` (Bolt on `7687`)
- FastAPI on port `8000`

### 3. Run the ETL Process

```bash
docker compose exec app python etl.py
```

### 4. Verify Everything Works

```bash
docker compose run --rm checks
```

##  Project Structure

```
.
├── app/
│   ├── Dockerfile              # FastAPI application container
│   ├── etl.py                  # Main ETL pipeline with helper functions
│   ├── main.py                 # FastAPI application
│   ├── queries.cypher          # Neo4j schema definitions
│   ├── requirements.txt        # Python dependencies
│   └── start.sh                # Application startup script
├── scripts/
│   ├── Dockerfile              # Checks service container
│   └── check_containers.sh    # End-to-end validation script
├── postgres/
│   └── init/
│       ├── 01_schema.sql       # Database schema
│       └── 02_seed.sql         # Sample data
├── neo4j/
│   ├── data/                   # Neo4j data persistence
│   └── import/                 # Import directory
├── assets/                     # Documentation images
├── docker-compose.yaml         # Service orchestration
└── README.md                   # This file
```

## 🔧 Configuration

### Environment Variables

The ETL script supports environment variable configuration:

**PostgreSQL:**
- `POSTGRES_HOST` (default: `postgres`)
- `POSTGRES_PORT` (default: `5432`)
- `POSTGRES_DB` (default: `shop`)
- `POSTGRES_USER` (default: `myuser`)
- `POSTGRES_PASSWORD` (default: `mypassword`)

**Neo4j:**
- `NEO4J_URI` (default: `bolt://neo4j:7687`)
- `NEO4J_USER` (default: `neo4j`)
- `NEO4J_PASSWORD` (default: `yourStrongPassword123`)

### Database Credentials

**PostgreSQL:**
- User: `myuser`
- Password: `mypassword`
- Database: `shop`

**Neo4j:**
- User: `neo4j`
- Password: `yourStrongPassword123`
- Browser: http://localhost:7474


### FastAPI Service

**Base URL:** http://localhost:8000

- `GET /` - Root endpoint
  ```json
  {"status": "ok"}
  ```

- `GET /health` - Health check
  ```json
  {"ok": true}
  ```


### Running the ETL

```bash
# From host machine
docker compose exec app python etl.py

# Or from within the container
docker compose exec app bash
python etl.py
```

The ETL process:
1. Waits for both databases to be ready
2. Creates Neo4j schema (constraints and indexes)
3. Extracts data from PostgreSQL
4. Transforms data into nodes and relationships
5. Loads data into Neo4j in batches
6. Reports completion status

##  Testing

### Automated End-to-End Tests

Run the comprehensive test suite:

```bash
docker compose run --rm checks
```

This will:
-  Check FastAPI health endpoint
-  Verify PostgreSQL connectivity and queries
-  Execute the ETL process
-  Validate all outputs

### Manual Testing

**Test PostgreSQL:**
```bash
docker compose exec postgres psql -U myuser -d shop -c "SELECT * FROM orders LIMIT 5;"
```

**Test Neo4j:**
- Open Neo4j Browser: http://localhost:7474
- Login with credentials: `neo4j` / `yourStrongPassword123`
- Run queries like:
  ```cypher
  MATCH (c:Customer)-[:PLACED]->(o:Order)-[:CONTAINS]->(p:Product)
  RETURN c.name, o.id, p.name
  LIMIT 10
  ```

**Test FastAPI:**
```bash
curl http://localhost:8000/health
```

##  Example Queries

### Find Products Purchased Together

```cypher
MATCH (p1:Product)<-[:CONTAINS]-(o:Order)-[:CONTAINS]->(p2:Product)
WHERE p1.id < p2.id
RETURN p1.name, p2.name, count(*) as frequency
ORDER BY frequency DESC
LIMIT 10
```

### Customer Purchase History

```cypher
MATCH (c:Customer)-[:PLACED]->(o:Order)-[:CONTAINS]->(p:Product)
WHERE c.id = 'C1'
RETURN c.name, o.id, p.name, p.price
ORDER BY o.id
```

### Product Recommendations Based on Events

```cypher
MATCH (c:Customer)-[:DID]->(e:Event)-[:ON]->(p:Product)
WHERE e.eventType = 'view'
RETURN c.name, p.name, count(*) as views
ORDER BY views DESC
LIMIT 10
```

##  Docker Commands

### Start Services
```bash
docker compose up -d
```

### Stop Services
```bash
docker compose down
```

### View Logs
```bash
docker compose logs -f app
```

### Rebuild Services
```bash
docker compose build
```

### Clean Everything (including volumes)
```bash
docker compose down -v
```

##  Troubleshooting

### Services Won't Start

1. Check if ports are already in use:
   ```bash
   lsof -i :5432  # PostgreSQL
   lsof -i :7474  # Neo4j Browser
   lsof -i :8000  # FastAPI
   ```

2. Check Docker logs:
   ```bash
   docker compose logs postgres
   docker compose logs neo4j
   docker compose logs app
   ```

### ETL Fails

1. Ensure both databases are ready:
   ```bash
   docker compose ps
   ```

2. Check database connectivity:
   ```bash
   docker compose exec app python -c "import psycopg2; psycopg2.connect(host='postgres', user='myuser', password='mypassword', dbname='shop')"
   ```

3. Verify Neo4j is accessible:
   ```bash
   curl http://localhost:7474
   ```

### Reset Everything

```bash
docker compose down -v
docker compose up -d
docker compose exec app python etl.py
```


  ##  Screenshots

![Graph Visualization](image2.jpeg)

![ETL Execution](image3.jpeg)

![Service Architecture](assets/Screenshot%202025-11-08%20at%2018.02.38.png)

![ETL Execution](assets/Screenshot%202025-11-08%20at%2018.02.57.png)




