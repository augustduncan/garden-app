import sqlite3
from pathlib import Path

import pandas as pd

MIGRATIONS = Path("migrations")

def rebuild(db_path):
    conn = sqlite3.connect(db_path)

    for sql_file in sorted(MIGRATIONS.glob("*.sql")):
        conn.executescript(sql_file.read_text())
        print("ran", sql_file.name)

    conn.commit()
    conn.close()

# Lets us run it by hand too:  python rebuild.py
if __name__ == "__main__":
    Path("garden.db").unlink(missing_ok=True)
    rebuild("garden.db")
