import sqlite3
import os

db_path = 'E:/Otomasyon/backend/company.db'
backup_path = 'E:/Otomasyon/backend/company_corrupted.db'
new_db_path = 'E:/Otomasyon/backend/company_new.db'

print(f"Backing up {db_path} to {backup_path}")
try:
    with open(db_path, 'rb') as f_in, open(backup_path, 'wb') as f_out:
        f_out.write(f_in.read())
except Exception as e:
    print(f"Failed to copy db: {e}")

print("Attempting to dump data...")
try:
    con = sqlite3.connect(db_path)
    with open('dump.sql', 'w', encoding='utf-8') as f:
        for line in con.iterdump():
            f.write('%s\n' % line)
    con.close()
    
    # Rebuild from dump
    print("Rebuilding database...")
    if os.path.exists(new_db_path):
        os.remove(new_db_path)
    
    new_con = sqlite3.connect(new_db_path)
    with open('dump.sql', 'r', encoding='utf-8') as f:
        sql = f.read()
    new_con.executescript(sql)
    new_con.commit()
    new_con.close()
    
    print("Replacing old db with recovered db...")
    if os.path.exists(db_path):
        os.remove(db_path)
    os.rename(new_db_path, db_path)
    print("Database recovered successfully!")

except Exception as e:
    print(f"Recovery failed: {e}")

