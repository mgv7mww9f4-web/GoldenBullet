import sqlite3

horse_name = input("Horse name: ")
race_number = int(input("Race number: "))
odds = float(input("Odds: "))
stake = float(input("Stake: "))
result = input("Result, win or lose: ").lower()

if result == "win":
    profit_loss = stake * (odds - 1)
elif result == "lose":
    profit_loss = -stake
else:
    print("Invalid result. Type win or lose.")
    exit()

conn = sqlite3.connect("goldenbullet.db")
cursor = conn.cursor()

cursor.execute("""
INSERT INTO bet_history
(horse_name, race_number, odds, stake, result, profit_loss)
VALUES (?, ?, ?, ?, ?, ?)
""", (horse_name, race_number, odds, stake, result, profit_loss))

cursor.execute("SELECT current_bankroll FROM bankroll LIMIT 1")
bankroll = cursor.fetchone()[0]

new_bankroll = bankroll + profit_loss

cursor.execute("""
UPDATE bankroll
SET current_bankroll = ?
WHERE id = 1
""", (new_bankroll,))

conn.commit()
conn.close()

print(f"Bet saved. Profit/Loss: ${profit_loss:.2f}")
print(f"New bankroll: ${new_bankroll:.2f}")