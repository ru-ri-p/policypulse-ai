# ingestion/db.py
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()


def get_connection():
    """Returns a live connection to the policypulse database."""
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        port=os.getenv("DB_PORT", "5432"),
    )


def run_query(sql, params=None, fetch=False):
    """
    Runs a SQL query.
    sql: the SQL string, e.g. "SELECT * FROM documents WHERE id = %s"
    params: values to substitute safely (prevents SQL injection)
    fetch: if True, return rows; if False, commit (INSERT/UPDATE/DELETE)
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(sql, params)
        results = cursor.fetchall() if fetch else None
        conn.commit()
        return results
    finally:
        cursor.close()
        conn.close()
