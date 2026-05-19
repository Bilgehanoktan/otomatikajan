import sqlite3

def check_tables():
    conn = sqlite3.connect('runtime/data/cortex_local_v2.db')
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("Tables in database:")
    for table in tables:
        print(f"- {table[0]}")
    conn.close()

if __name__ == "__main__":
    check_tables()
