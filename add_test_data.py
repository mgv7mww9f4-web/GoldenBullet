import sqlite3

conn = sqlite3.connect("goldenbullet.db")
cursor = conn.cursor()

runners = [
    # horse_number, horse_name, race_number, grade, barrier, jockey, trainer, odds,
    # last_start, second_last, third_last,
    # distance_wins, distance_runs, track_wins, track_runs,
    # weight_carried, race_distance, track_condition

    (2, "Fast Star", 1, "Grade 4", 2, "J. Smith", "P. Jones", 4.50,
     4, 3, 5,
     1, 4, 0, 2,
     57.5, 1200, "Good"),

    (5, "Speed King", 1, "Grade 4", 5, "B. Brown", "L. White", 3.20,
     2, 2, 1,
     2, 5, 1, 3,
     56.0, 1200, "Good"),

    (1, "Storm Horse", 2, "Grade 5", 1, "C. Green", "A. Lee", 15.00,
     5, 4, 3,
     0, 3, 1, 4,
     58.0, 1400, "Soft"),

    (4, "Golden Lad", 2, "Grade 5", 4, "D. Black", "M. Stone", 5.50,
     1, 2, 2,
     3, 6, 2, 4,
     55.5, 1400, "Soft"),
]

cursor.executemany("""
INSERT INTO runners
(horse_number, horse_name, race_number, grade, barrier, jockey, trainer, odds,
 last_start_position, second_last_position, third_last_position,
 distance_wins, distance_runs, track_wins, track_runs,
 weight_carried, race_distance, track_condition)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""", runners)

conn.commit()
conn.close()

print("Test runners with full racing data added")