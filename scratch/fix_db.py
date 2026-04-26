import sqlite3
import os

db_path = r'E:\ai_company_faz12.1\runtime\data\cortex_local.db'

def add_column(table, column, type):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {type}")
        conn.commit()
        conn.close()
        print(f"Added {column} to {table}")
    except Exception as e:
        print(f"Error adding {column} to {table}: {e}")

add_column("decision_lineage", "outcome", "TEXT")
add_column("improvement_opportunities", "affected_files", "TEXT")
