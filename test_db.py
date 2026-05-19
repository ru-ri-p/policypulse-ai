# test_db.py — Week 1 Day 6: connection check using .env credentials
import os

import psycopg2
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(
    host=os.getenv("DB_HOST"),
    database=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    port=os.getenv("DB_PORT", "5432"),
)

cursor = conn.cursor()
cursor.execute("SELECT version();")
result = cursor.fetchone()
print("Connected to:", result[0])

cursor.close()
conn.close()
