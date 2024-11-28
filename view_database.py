"""Script to view database contents."""

import os
import json
from datetime import datetime
from dotenv import load_dotenv
import sqlite3
from typing import Dict, List

def print_table_contents(db_path: str, table_name: str):
    """Print all contents of a specified table."""
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        # Get column names
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [col[1] for col in cursor.fetchall()]
        print(f"\n=== Contents of {table_name} ===")
        print("Columns:", ", ".join(columns))
        
        # Get all rows
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()
        print(f"Total rows: {len(rows)}")
        
        # Print each row
        for row in rows:
            print("\nRow:")
            for col, val in zip(columns, row):
                # Format JSON fields for better readability
                if isinstance(val, str) and (val.startswith('{') or val.startswith('[')):
                    try:
                        val = json.dumps(json.loads(val), indent=2)
                    except:
                        pass
                print(f"  {col}: {val}")
            print("-" * 50)

def main():
    """Display contents of the database."""
    db_path = "reddit_memory.db"
    
    # Tables we want to examine
    tables = [
        "submissions",
        "learned_patterns",
        "action_outcomes"
    ]
    
    print(f"Examining database: {db_path}")
    
    try:
        # Print contents of each table
        for table in tables:
            try:
                print_table_contents(db_path, table)
            except sqlite3.Error as e:
                print(f"Error reading table {table}: {str(e)}")
    
    except sqlite3.Error as e:
        print(f"Database error: {str(e)}")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
