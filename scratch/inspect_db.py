import sqlite3

def main():
    conn = sqlite3.connect("runtime/data/cortex_local_v2.db")
    cursor = conn.cursor()
    cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='table' AND (name LIKE 'ui_repair%' OR name LIKE '%pr_review%')")
    rows = cursor.fetchall()
    for name, sql in rows:
        print(f"Table: {name}")
        print(sql)
        print("-" * 50)
    conn.close()

if __name__ == "__main__":
    main()
