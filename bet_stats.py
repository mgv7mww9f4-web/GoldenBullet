import sqlite3

conn = sqlite3.connect("goldenbullet.db")
cursor = conn.cursor()

cursor.execute("SELECT COUNT(*) FROM bet_history")
total_bets = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM bet_history WHERE result = 'win'")
wins = cursor.fetchone()[0]

cursor.execute("SELECT SUM(stake) FROM bet_history")
total_staked = cursor.fetchone()[0] or 0

cursor.execute("SELECT SUM(profit_loss) FROM bet_history")
total_profit = cursor.fetchone()[0] or 0

if total_bets > 0:
    strike_rate = (wins / total_bets) * 100
else:
    strike_rate = 0

if total_staked > 0:
    roi = (total_profit / total_staked) * 100
else:
    roi = 0

print("BETTING STATS")
print("-------------")
print(f"Total Bets: {total_bets}")
print(f"Wins: {wins}")
print(f"Strike Rate: {strike_rate:.1f}%")
print(f"Total Staked: ${total_staked:.2f}")
print(f"Profit/Loss: ${total_profit:.2f}")
print(f"ROI: {roi:.1f}%")

conn.close()