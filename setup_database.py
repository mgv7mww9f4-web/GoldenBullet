import sqlite3

conn = sqlite3.connect("goldenbullet.db")
cursor = conn.cursor()

cursor.execute("DROP TABLE IF EXISTS runners")

cursor.execute("""
CREATE TABLE runners (
    id INTEGER PRIMARY KEY,

    horse_number INTEGER,
    horse_name TEXT,
    race_number INTEGER,
    grade TEXT,

    barrier INTEGER,
    jockey TEXT,
    trainer TEXT,
    odds REAL,

    last_start_position INTEGER,
    second_last_position INTEGER,
    third_last_position INTEGER,

    distance_range TEXT,
    weight_carried REAL,
    track_condition TEXT,
    weather TEXT,

    sky_rating INTEGER,

    sky_rating_score INTEGER,
    form_score INTEGER,
    distance_score INTEGER,
    track_score INTEGER,
    barrier_score INTEGER,
    jockey_score INTEGER,
    trainer_score INTEGER,
    grade_score INTEGER,
    weight_score INTEGER,
    market_score INTEGER,

    score INTEGER
)
""")

conn.commit()
conn.close()

print("Database ready with full score breakdown")