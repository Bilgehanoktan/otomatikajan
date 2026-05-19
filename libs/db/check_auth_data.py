import sqlite3


def check_operators():
    conn = sqlite3.connect("runtime/data/cortex_local.db")
    cursor = conn.cursor()

    print("--- Operators ---")
    cursor.execute("SELECT id, email, role, is_active FROM operators")
    for row in cursor.fetchall():
        print(row)

    print("\n--- Users (Old) ---")
    try:
        cursor.execute("SELECT id, email, is_admin FROM users")
        for row in cursor.fetchall():
            print(row)
    except:
        print("Users table not accessible or empty.")

    conn.close()

if __name__ == "__main__":
    check_operators()
