FROM python:3.11-slim

# Install curl and postgresql client
RUN apt-get update && apt-get install -y \
    curl \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies needed for ETL
RUN pip install --no-cache-dir \
    neo4j \
    psycopg2-binary

WORKDIR /scripts

COPY check_containers.sh /scripts/
RUN chmod +x /scripts/check_containers.sh

CMD ["sh", "check_containers.sh"]

