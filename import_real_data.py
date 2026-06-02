import sqlite3

horses = [
    [13, "Zavega", 6, "BM58", 1, "Ben Looker", "Alyssa and Troy Sweeney", 3.50, 1, 3, 1, "800m-1000m", 57.0, "Soft 7", "Fine", 100],
    [3, "Irish Jig", 6, "BM58", 8, "Mikayla Weir", "Scott Singleton", 3.20, 1, 6, 4, "1200m-1280m", 62.0, "Soft 7", "Fine", 93],
    [4, "Imperial State", 6, "BM58", 6, "Angel Brennan", "Craig Martin", 4.60, 5, 5, 4, "1100m", 61.5, "Soft 7", "Fine", 82],
    [10, "Exoflow", 6, "BM58", 4, "Kody Nestor", "Ridge Wilson", 7.50, 2, 4, 8, "850m-1015m", 58.0, "Soft 7", "Fine", 82],
    [12, "Dubalene", 6, "BM58", 5, "Luke Rolls", "Colt Prosser", 8.50, 1, 2, 3, "800m-1400m", 57.5, "Soft 7", "Fine", 80],
    [1, "Elusive Eagle", 6, "BM58", 2, "Jasmine Urquhart-Warren", "Barry Sheppard", 14.00, 8, 4, 1, "950m-1200m", 65.0, "Soft 7", "Fine", 75],
    [8, "Hit Song", 6, "BM58", 9, "Madeline Owen", "Nikki Pollock", 23.00, 5, 0, 2, "1200m", 59.0, "Soft 7", "Fine", 63],
    [15, "Gold Smiles", 6, "BM58", 7, "Leanne Boyd", "Sally Torrens", 19.00, 5, 9, 7, "1100m", 55.0, "Soft 7", "Fine", 64],
    [14, "Evony", 6, "BM58", 3, "Grace Palmer", "Paddy Cunningham", 26.00, 2, 1, 7, "1183m", 55.0, "Soft 7", "Fine", 33],
    [16, "Little Show", 6, "BM58", 10, "Zoe Hunt", "Gino Barbierato", 126.00, 5, 6, 7, "840m-1200m", 55.0, "Soft 7", "Fine", 27],
]

conn = sqlite3.connect("goldenbullet.db")
cursor = conn.cursor()

cursor.execute("DELETE FROM runners")

cursor.executemany("""
INSERT INTO runners (
    horse_number,
    horse_name,
    race_number,
    grade,
    barrier,
    jockey,
    trainer,
    odds,
    last_start_position,
    second_last_position,
    third_last_position,
    distance_range,
    weight_carried,
    track_condition,
    weather,
    sky_rating,
    score
)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
""", horses)

conn.commit()
conn.close()

print("Real race data imported successfully")