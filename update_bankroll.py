import sqlite3

result = input("Did the bet win or lose? Type win or lose: ")
stake = float(input("Enter stake amount: "))
odds = float(input("Enter odds: "))

conn = sqlite3.connect("goldenbullet.db")
cursor = conn.cursor()

cursor.execute("SELECT current_bankroll FROM bankroll LIMIT 1")
bankroll = cursor.fetchone()[0]

if result == "win":
    profit = stake * (odds - 1)
    bankroll = bankroll + profit
elif result == "lose":
    bankroll = bankroll - stake
else:
    print("Invalid result. Type win or lose.")
    conn.close()
    exit()

cursor.execute("""
UPDATE bankroll
SET current_bankroll = ?
WHERE id = 1
""", (bankroll,))

conn.commit()
conn.close()

print(f"Updated bankroll: ${bankroll:.2f}")