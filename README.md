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

![Service Architecture](assets/Screenshot%202025-11-08%20at%2018.02.38.png)

##  Features

- **ETL Pipeline**: Automated data extraction, transformation, and loading
- **Graph Modeling**: Converts relational data into graph structures (Customers, Products, Orders, Events)
- **Batch Processing**: Efficient chunk-based data loading
- **Idempotent Operations**: Safe to run multiple times using MERGE operations
- **Health Monitoring**: FastAPI health endpoints for service monitoring
- **Automated Testing**: End-to-end validation script
- **Docker Compose**: One-command deployment

## 📋 Prerequisites

- Docker and Docker Compose installed
- At least 4GB of available RAM
- Ports 5432, 7474, 7687, and 8000 available

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

![ETL Execution](assets/Screenshot%202025-11-08%20at%2018.02.57.png)

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

## 📊 Data Model

### PostgreSQL Schema

- **customers** - Customer information
- **categories** - Product categories
- **products** - Product catalog
- **orders** - Order transactions
- **order_items** - Order line items
- **events** - Customer behavioral events (views, clicks, cart additions)

### Neo4j Graph Model

**Nodes:**
- `Customer` - Customer entities
- `Product` - Product entities
- `Category` - Product categories
- `Order` - Order entities
- `Event` - Behavioral events

**Relationships:**
- `PLACED` - Customer → Order
- `CONTAINS` - Order → Product (with quantity)
- `BELONGS_TO` - Product → Category
- `DID` - Customer → Event
- `ON` - Event → Product

## 🔌 API Endpoints

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

## 🛠️ ETL Process

The ETL pipeline (`app/etl.py`) includes the following helper functions:

### Core Functions

- `wait_for_postgres()` - Waits for PostgreSQL to be ready
- `wait_for_neo4j()` - Waits for Neo4j to be ready
- `run_cypher(query)` - Executes a single Cypher query
- `run_cypher_file(file_path)` - Executes multiple Cypher statements from a file
- `chunk(data, chunk_size)` - Splits data into batches for processing
- `extract_data_from_postgres()` - Extracts all tables from PostgreSQL
- `transform_data_to_neo4j(tables)` - Transforms relational data to graph format
- `load_data_to_neo4j(nodes, relationships)` - Loads data into Neo4j
- `etl()` - Main ETL orchestration function

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

## 🧪 Testing

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

## 🔍 Troubleshooting

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

## Technologies

- **PostgreSQL 16** - Relational database
- **Neo4j 5** - Graph database with APOC and GDS plugins
- **FastAPI** - Modern Python web framework
- **Python 3.11** - Programming language
- **Docker Compose** - Container orchestration
- **psycopg2** - PostgreSQL adapter
- **neo4j** - Neo4j Python driver

##  Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test with `docker compose run --rm checks`
5. Submit a pull request

## License

This project is open source and available under the MIT License.

## Acknowledgments

- Neo4j for the graph database platform
- FastAPI for the excellent web framework
- Docker for containerization

  ## 🖼️ Screenshots

### Data Model Diagram

![Data Model](assets/image1.jpeg)

### Example Graph Visualization

![Graph Visualization](assets/image2.jpeg)

### ETL Process Execution

![ETL Execution](assets/image3.jpeg)


