import json
import shutil
import sqlite3
import time
import uuid
from contextlib import closing
from datetime import datetime, timezone

from flask import Flask, Response, g, request
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)

app = Flask(__name__)
DATABASE = "/app/lab.db"

REQUESTS = Counter(
    "app_http_requests_total",
    "HTTP requests excluding metrics and health checks",
    ["method", "route", "status"],
)

LATENCY = Histogram(
    "app_http_request_duration_seconds",
    "HTTP request duration excluding metrics and health checks",
    ["method", "route"],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2, 5],
)

DB_HEALTH = Gauge(
    "app_db_connection_success",
    "Whether the latest SQLite connection and SELECT 1 succeeded",
)

DB_QUERIES = Counter(
    "app_db_queries_total",
    "Database operations from application requests",
    ["result"],
)

DB_LATENCY = Histogram(
    "app_db_query_duration_seconds",
    "Database operation duration including connection setup",
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.5, 1],
)

DISK_TOTAL = Gauge(
    "app_filesystem_total_bytes",
    "Total filesystem space visible at /app",
)

DISK_FREE = Gauge(
    "app_filesystem_free_bytes",
    "Free filesystem space visible at /app",
)

# Initialize both results so zero errors can be measured.
DB_QUERIES.labels("success")
DB_QUERIES.labels("error")


def execute_sql(sql):
    with closing(sqlite3.connect(DATABASE, timeout=2)) as connection:
        return connection.execute(sql).fetchone()


@app.before_request
def start_request():
    g.started = time.perf_counter()
    g.request_id = str(uuid.uuid4())
    g.error_code = None


@app.after_request
def record_request(response):
    response.headers["X-Request-ID"] = g.request_id

    if request.path in ("/metrics", "/health"):
        return response

    duration = time.perf_counter() - g.started
    route = request.url_rule.rule if request.url_rule else "unmatched"

    REQUESTS.labels(
        request.method, route, str(response.status_code)
    ).inc()
    LATENCY.labels(request.method, route).observe(duration)

    error_code = g.error_code
    if response.status_code >= 500 and error_code is None:
        error_code = "HTTP_5XX"

    print(
        json.dumps({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": "ERROR" if response.status_code >= 500 else "INFO",
            "service": "practice-app",
            "request_id": g.request_id,
            "method": request.method,
            "route": route,
            "status": response.status_code,
            "duration_seconds": round(duration, 6),
            "error_code": error_code,
        }),
        flush=True,
    )

    return response


@app.get("/")
def home():
    return {"message": "Practice application is running"}


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.get("/fail")
def fail():
    g.error_code = "SIMULATED_FAILURE"
    return {"error": "Deliberate failure for the lab"}, 500


@app.get("/slow")
def slow():
    time.sleep(1)
    return {"message": "Deliberately slow response"}


def database_request(sql):
    started = time.perf_counter()
    try:
        result = execute_sql(sql)
        DB_QUERIES.labels("success").inc()
        return {"result": result[0]}
    except sqlite3.Error:
        DB_QUERIES.labels("error").inc()
        g.error_code = "DATABASE_QUERY_FAILED"
        return {"error": "Database query failed"}, 500
    finally:
        DB_LATENCY.observe(time.perf_counter() - started)


@app.get("/db")
def database_success():
    return database_request("SELECT 1")


@app.get("/db-fail")
def database_failure():
    return database_request("SELECT * FROM deliberately_missing_table")


@app.get("/metrics")
def metrics():
    # Check database connectivity separately from application query errors.
    try:
        execute_sql("SELECT 1")
        DB_HEALTH.set(1)
    except sqlite3.Error:
        DB_HEALTH.set(0)

    disk = shutil.disk_usage("/app")
    DISK_TOTAL.set(disk.total)
    DISK_FREE.set(disk.free)

    return Response(generate_latest(), content_type=CONTENT_TYPE_LATEST)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=False)