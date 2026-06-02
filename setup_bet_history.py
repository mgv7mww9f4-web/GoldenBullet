import sqlite3

conn = sqlite3.connect("goldenbullet.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS bet_history (
    id INTEGER PRIMARY KEY,
    horse_name TEXT,
    race_number INTEGER,
    odds REAL,
    stake REAL,
    result TEXT,
    profit_loss REAL
)
""")

conn.commit()
conn.close()

print("Bet history table created")