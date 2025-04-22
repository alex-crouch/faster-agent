#!/usr/bin/env python3
"""
Initialize the SQLite database for MCP server configurations.
"""

import os
import sqlite3
import sys

DB_FILE = "mcp_servers.db"
SCHEMA_FILE = "schema.sql"


def initialize_db():
    """Create the database and initialize it with schema and sample data."""
    if os.path.exists(DB_FILE):
        print(f"Database file {DB_FILE} already exists. Delete it first if you want to recreate.")
        return 1

    print(f"Creating database {DB_FILE}...")

    # Check if schema file exists
    if not os.path.exists(SCHEMA_FILE):
        print(f"Error: Schema file {SCHEMA_FILE} not found.")
        return 1

    # Read schema file
    with open(SCHEMA_FILE, "r") as f:
        schema_sql = f.read()

    # Create database and execute schema
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.executescript(schema_sql)
        conn.commit()
        print("Database initialized successfully.")

        # Verify the tables were created
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print("Created tables:")
        for table in tables:
            print(f"- {table[0]}")

        # Count records in each table
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table[0]};")
            count = cursor.fetchone()[0]
            print(f"  {table[0]}: {count} records")

        conn.close()
        return 0
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(initialize_db())
