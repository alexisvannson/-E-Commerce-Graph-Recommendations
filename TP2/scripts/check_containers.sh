#!/bin/sh

set -e

echo "Waiting for services to be ready..."
sleep 5

# Wait for FastAPI
max_attempts=30
attempt=0
while [ $attempt -lt $max_attempts ]; do
    if curl -s http://app:8000/health > /dev/null 2>&1; then
        break
    fi
    attempt=$((attempt + 1))
    sleep 2
done

if [ $attempt -eq $max_attempts ]; then
    echo "✗ FastAPI did not become ready in time"
    exit 1
fi

# Check FastAPI health
echo "› FastAPI: GET /health"
health_response=$(curl -s http://app:8000/health)
echo "$health_response"
if echo "$health_response" | grep -q '"ok":true'; then
    echo "✔ FastAPI health OK"
else
    echo "✗ FastAPI health check failed"
    exit 1
fi

# Check Postgres orders
echo ""
echo "› Postgres: SELECT * FROM orders LIMIT 5;"
PGPASSWORD=mypassword psql -h postgres -U myuser -d shop -c "SELECT * FROM orders LIMIT 5;" 2>&1
if [ $? -eq 0 ]; then
    echo "✔ Orders query OK"
else
    echo "✗ Orders query failed"
    exit 1
fi

# Check Postgres now()
echo ""
echo "› Postgres: SELECT now();"
PGPASSWORD=mypassword psql -h postgres -U myuser -d shop -c "SELECT now();" 2>&1
if [ $? -eq 0 ]; then
    echo "✔ now() query OK"
else
    echo "✗ now() query failed"
    exit 1
fi

# Run ETL
echo ""
echo "› ETL: python /work/app/etl.py"
# Run ETL and capture output, show only if there's an error or show success message
if python /work/app/etl.py > /tmp/etl_output.log 2>&1; then
    # Check if ETL completed successfully
    if grep -q "ETL process completed successfully" /tmp/etl_output.log; then
        echo "ETL done."
        echo "✔ ETL output OK (ETL done.)"
    else
        cat /tmp/etl_output.log
        echo "✗ ETL did not complete successfully"
        exit 1
    fi
else
    cat /tmp/etl_output.log
    echo "✗ ETL failed"
    exit 1
fi
