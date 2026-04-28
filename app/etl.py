"""
Mini ETL job:
  1. Read sample sales data from CSV
  2. Load it into the PostgreSQL `sales` table
  3. Run an aggregation query and print the result

Connection details come from environment variables that are wired up by
docker-compose, so the script needs no editing to run inside the container.
"""

import csv
import os
import sys
import time

import psycopg2
from psycopg2.extras import execute_values


def get_connection(retries: int = 10, delay: int = 2):
    """Open a connection to PostgreSQL, retrying until the DB is ready."""
    last_err = None
    for attempt in range(1, retries + 1):
        try:
            conn = psycopg2.connect(
                host=os.environ["POSTGRES_HOST"],
                port=os.environ["POSTGRES_PORT"],
                user=os.environ["POSTGRES_USER"],
                password=os.environ["POSTGRES_PASSWORD"],
                dbname=os.environ["POSTGRES_DB"],
            )
            print(f"[ETL] Connected to PostgreSQL on attempt {attempt}.")
            return conn
        except psycopg2.OperationalError as err:
            last_err = err
            print(f"[ETL] Postgres not ready (attempt {attempt}/{retries}): {err}")
            time.sleep(delay)
    raise RuntimeError(f"Could not connect to Postgres: {last_err}")


def load_csv(path: str):
    """Read the CSV file and return a list of tuples ready for INSERT."""
    rows = []
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append((
                row["product"],
                row["category"],
                int(row["quantity"]),
                float(row["unit_price"]),
                row["sale_date"],
            ))
    return rows


def insert_rows(conn, rows):
    """Bulk-insert rows into the sales table."""
    sql = """
        INSERT INTO sales (product, category, quantity, unit_price, sale_date)
        VALUES %s
    """
    with conn.cursor() as cur:
        # Truncate so the script is idempotent across re-runs
        cur.execute("TRUNCATE TABLE sales RESTART IDENTITY;")
        execute_values(cur, sql, rows)
    conn.commit()
    print(f"[ETL] Inserted {len(rows)} rows into sales.")


def report(conn):
    """Run a small aggregation query so you can see the data round-trip."""
    sql = """
        SELECT category,
               COUNT(*)                              AS line_items,
               SUM(quantity)                         AS total_units,
               ROUND(SUM(quantity * unit_price), 2)  AS total_revenue
        FROM sales
        GROUP BY category
        ORDER BY total_revenue DESC;
    """
    with conn.cursor() as cur:
        cur.execute(sql)
        results = cur.fetchall()

    print("\n[ETL] Revenue by category")
    print("-" * 60)
    print(f"{'Category':<15}{'Lines':>10}{'Units':>10}{'Revenue ($)':>20}")
    print("-" * 60)
    for category, lines, units, revenue in results:
        print(f"{category:<15}{lines:>10}{units:>10}{float(revenue):>20,.2f}")
    print("-" * 60)


def main():
    csv_path = os.path.join(os.path.dirname(__file__), "data.csv")
    rows = load_csv(csv_path)
    print(f"[ETL] Loaded {len(rows)} rows from {csv_path}.")

    conn = get_connection()
    try:
        insert_rows(conn, rows)
        report(conn)
    finally:
        conn.close()
        print("[ETL] Done.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"[ETL] FAILED: {exc}", file=sys.stderr)
        sys.exit(1)
