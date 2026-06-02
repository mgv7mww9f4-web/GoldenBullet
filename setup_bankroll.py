import sqlite3

conn = sqlite3.connect("goldenbullet.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS bankroll (
    id INTEGER PRIMARY KEY,
    current_bankroll REAL
)
""")

cursor.execute("DELETE FROM bankroll")

cursor.execute("""
INSERT INTO bankroll (current_bankroll)
VALUES (100)
""")

conn.commit()
conn.close()

print("Bankroll table created")