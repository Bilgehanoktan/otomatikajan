
import os
from libs.db.session import get_engine

def diagnose_path():
    engine = get_engine()
    print(f"Engine URL: {engine.url}")

if __name__ == "__main__":
    diagnose_path()
