import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st

DB = Path("garden.db")

# Build the database the first time the app runs (or after a restart wipes it) (or the reset button !!)
if not DB.exists():
    conn = sqlite3.connect(DB)
    conn.executescript("""
        CREATE TABLE bed (
            bed_id   INTEGER PRIMARY KEY,
            crop     TEXT NOT NULL,
            location TEXT
        );
        CREATE TABLE bed_log (
            log_id   INTEGER PRIMARY KEY,
            bed_id   INTEGER NOT NULL REFERENCES bed(bed_id),
            log_date TEXT,
            status   TEXT
        );
        INSERT INTO bed VALUES
            (1, 'kale', 'upper garden'),
            (2, 'garlic', 'hoop house'),
            (3, 'tomatoes', 'lower garden');
        INSERT INTO bed_log (bed_id, log_date, status) VALUES
            (1, '2026-09-01', 'seeded'),
            (1, '2026-09-20', 'sprouting'),
            (2, '2026-09-05', 'seeded');
    """)
    conn.commit()
    conn.close()

conn = sqlite3.connect(DB)

# foreign keys on -- this will not allow you to remove beds that have existing entries
conn.execute('PRAGMA foreign_keys = ON') 

st.title("garden beds :D ")

# RESET: throw away garden.db so the app builds a fresh one
if st.button("reset!"):
    conn.close()
    DB.unlink()
    st.rerun()

# READ: pick a bed, see its history
crops = pd.read_sql_query("SELECT crop FROM bed ORDER BY crop", conn)["crop"]
crop = st.selectbox("which bed?", crops)

history = pd.read_sql_query(
    """
    SELECT l.log_date, l.status
    FROM bed_log l
    JOIN bed b ON b.bed_id = l.bed_id
    WHERE b.crop = ?
    ORDER BY l.log_date
    """,
    conn,
    params=(crop,),
)
st.dataframe(history, hide_index=True)

# CREATE: add a visit for this bed
with st.form("add_visit"):
    visit_date = st.date_input("when?")
    status = st.selectbox("status?", ["seeded", "sprouting", "harvesting", "fallow", "failed"])
    if st.form_submit_button("add visit"):
        conn.execute(
            "INSERT INTO bed_log (bed_id, log_date, status) "
            "SELECT bed_id, ?, ? FROM bed WHERE crop = ?",
            (str(visit_date), status, crop),
        )
        conn.commit()
        st.rerun()

# UPDATE: fix the name of the bed we picked
with st.form("fix_crop"):
    new_crop = st.text_input("fix the name of this bed", value=crop)
    if st.form_submit_button("update!"):
        conn.execute("UPDATE bed SET crop = ? WHERE crop = ?", (new_crop, crop))
        conn.commit()
        st.rerun()



# DELETE: remove the bed we picked
with st.form("remove_bed"):
    st.write("remove the selected bed")
    if st.form_submit_button("REMOVE"):
        try:
            conn.execute("DELETE FROM bed WHERE crop = ?", (crop,))
            conn.commit()
            st.rerun()
        except sqlite3.IntegrityError:
            conn.rollback()
            st.error(f"can't delete {crop}: it still has logs!")
