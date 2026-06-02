import sqlite3


MAX_SCORE = 116


def get_rating_percentage(score):
    return round((score / MAX_SCORE) * 100, 1)


def get_bankroll(cursor):
    cursor.execute("SELECT current_bankroll FROM bankroll LIMIT 1")
    result = cursor.fetchone()

    if result:
        return result[0]

    return 100


def get_bet_stats(cursor):
    cursor.execute("SELECT COUNT(*) FROM bet_history")
    total_bets = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM bet_history WHERE result = 'win'")
    wins = cursor.fetchone()[0]

    cursor.execute("SELECT SUM(stake) FROM bet_history")
    total_staked = cursor.fetchone()[0] or 0

    cursor.execute("SELECT SUM(profit_loss) FROM bet_history")
    total_profit = cursor.fetchone()[0] or 0

    strike_rate = (wins / total_bets) * 100 if total_bets > 0 else 0
    roi = (total_profit / total_staked) * 100 if total_staked > 0 else 0

    return total_bets, wins, strike_rate, total_staked, total_profit, roi


def get_confidence(score):
    rating = get_rating_percentage(score)

    if rating >= 85:
        return "Elite"
    elif rating >= 75:
        return "Very High"
    elif rating >= 65:
        return "High"
    elif rating >= 55:
        return "Medium"
    else:
        return "Low"


def get_suggested_stake(score, bankroll):
    rating = get_rating_percentage(score)

    if rating >= 85:
        stake = bankroll * 0.05
    elif rating >= 75:
        stake = bankroll * 0.04
    elif rating >= 65:
        stake = bankroll * 0.03
    elif rating >= 55:
        stake = bankroll * 0.02
    else:
        stake = 0

    if stake == 0:
        return "No Bet"

    return f"${stake:.2f} win"


def get_roughie_stake(bankroll):
    return f"${bankroll * 0.01:.2f} each-way"


def add_score_breakdown(report_lines, runner):
    (
        sky_rating_score,
        form_score,
        distance_score,
        track_score,
        barrier_score,
        jockey_score,
        trainer_score,
        grade_score,
        weight_score,
        market_score
    ) = runner

    report_lines.append("")
    report_lines.append("Score Breakdown:")
    report_lines.append(f"- Sky Rating: {sky_rating_score}/15")
    report_lines.append(f"- Form: {form_score}/35")
    report_lines.append(f"- Distance: {distance_score}/10")
    report_lines.append(f"- Track: {track_score}/8")
    report_lines.append(f"- Barrier: {barrier_score}/8")
    report_lines.append(f"- Jockey: {jockey_score}/2")
    report_lines.append(f"- Trainer: {trainer_score}/2")
    report_lines.append(f"- Grade: {grade_score}/6")
    report_lines.append(f"- Weight: {weight_score}/10")
    report_lines.append(f"- Market/Odds: {market_score}/20")


def add_reason_lines(report_lines, score, odds):
    rating = get_rating_percentage(score)

    report_lines.append("")
    report_lines.append("Why:")

    if rating >= 75:
        report_lines.append("- Strong overall rating from the model")

    if odds <= 5:
        report_lines.append("- Strong market support")

    if 5 < odds <= 12:
        report_lines.append("- Decent price while still rating well")

    if odds >= 15:
        report_lines.append("- Longer-priced runner with enough score to consider")

    if rating < 55:
        report_lines.append("- Rating is low, so no serious stake recommended")


conn = sqlite3.connect("goldenbullet.db")
cursor = conn.cursor()

bankroll = get_bankroll(cursor)
total_bets, wins, strike_rate, total_staked, total_profit, roi = get_bet_stats(cursor)

report_lines = []

report_lines.append("GOLDEN BULLET DAILY REPORT")
report_lines.append("==========================")
report_lines.append("")
report_lines.append(f"Bankroll: ${bankroll:.2f}")
report_lines.append(f"Total Bets: {total_bets}")
report_lines.append(f"Wins: {wins}")
report_lines.append(f"Strike Rate: {strike_rate:.1f}%")
report_lines.append(f"Total Staked: ${total_staked:.2f}")
report_lines.append(f"Profit/Loss: ${total_profit:.2f}")
report_lines.append(f"ROI: {roi:.1f}%")
report_lines.append("")
report_lines.append("Reminder: This is analysis only. No tip is guaranteed.")
report_lines.append("")

report_lines.append("BEST TIP FOR EACH RACE")
report_lines.append("----------------------")

cursor.execute("""
SELECT r1.horse_number, r1.horse_name, r1.race_number,
       r1.grade, r1.odds, r1.score
FROM runners r1
WHERE r1.score = (
    SELECT MAX(r2.score)
    FROM runners r2
    WHERE r2.race_number = r1.race_number
)
ORDER BY r1.race_number
""")

for horse_number, horse, race, grade, odds, score in cursor.fetchall():
    report_lines.append(f"Race {race}: #{horse_number} {horse}")
    report_lines.append(f"Grade: {grade}")
    report_lines.append(f"Odds: ${odds}")
    report_lines.append(f"Score: {score}/{MAX_SCORE}")
    report_lines.append(f"Rating: {get_rating_percentage(score)}%")
    report_lines.append(f"Confidence: {get_confidence(score)}")
    report_lines.append(f"Suggested Stake: {get_suggested_stake(score, bankroll)}")
    report_lines.append("")

report_lines.append("TOP 3 CHANCES FOR EACH RACE")
report_lines.append("---------------------------")

cursor.execute("SELECT DISTINCT race_number FROM runners ORDER BY race_number")

for (race_number,) in cursor.fetchall():
    report_lines.append(f"Race {race_number}")

    cursor.execute("""
    SELECT horse_number, horse_name, odds, score
    FROM runners
    WHERE race_number = ?
    ORDER BY score DESC
    LIMIT 3
    """, (race_number,))

    position = 1

    for horse_number, horse, odds, score in cursor.fetchall():
        report_lines.append(
            f"{position}. #{horse_number} {horse} | "
            f"Odds ${odds} | "
            f"Score {score}/{MAX_SCORE} | "
            f"Rating {get_rating_percentage(score)}%"
        )
        position += 1

    report_lines.append("")

report_lines.append("GOLDEN BULLET TIP OF THE DAY")
report_lines.append("----------------------------")

cursor.execute("""
SELECT horse_number, horse_name, race_number,
       grade, odds, score,
       sky_rating_score, form_score, distance_score, track_score,
       barrier_score, jockey_score, trainer_score, grade_score,
       weight_score, market_score
FROM runners
WHERE score >= 65
ORDER BY score DESC
LIMIT 1
""")

golden_bullet = cursor.fetchone()

if golden_bullet:
    horse_number, horse, race, grade, odds, score = golden_bullet[:6]
    breakdown = golden_bullet[6:]

    report_lines.append(f"Race: {race}")
    report_lines.append(f"Horse: #{horse_number} {horse}")
    report_lines.append(f"Grade: {grade}")
    report_lines.append(f"Odds: ${odds}")
    report_lines.append(f"Score: {score}/{MAX_SCORE}")
    report_lines.append(f"Rating: {get_rating_percentage(score)}%")
    report_lines.append(f"Confidence: {get_confidence(score)}")
    report_lines.append(f"Suggested Stake: {get_suggested_stake(score, bankroll)}")

    add_score_breakdown(report_lines, breakdown)
    add_reason_lines(report_lines, score, odds)

else:
    report_lines.append("No Golden Bullet today")

report_lines.append("")

report_lines.append("ROUGHIE CHANCE OF THE DAY")
report_lines.append("-------------------------")

cursor.execute("""
SELECT horse_number, horse_name, race_number,
       grade, odds, score,
       sky_rating_score, form_score, distance_score, track_score,
       barrier_score, jockey_score, trainer_score, grade_score,
       weight_score, market_score
FROM runners
WHERE odds >= 15
AND score >= 65
ORDER BY score DESC
LIMIT 1
""")

roughie = cursor.fetchone()

if roughie:
    horse_number, horse, race, grade, odds, score = roughie[:6]
    breakdown = roughie[6:]

    report_lines.append(f"Race: {race}")
    report_lines.append(f"Horse: #{horse_number} {horse}")
    report_lines.append(f"Grade: {grade}")
    report_lines.append(f"Odds: ${odds}")
    report_lines.append(f"Score: {score}/{MAX_SCORE}")
    report_lines.append(f"Rating: {get_rating_percentage(score)}%")
    report_lines.append(f"Confidence: {get_confidence(score)}")
    report_lines.append(f"Suggested Stake: {get_roughie_stake(bankroll)}")

    add_score_breakdown(report_lines, breakdown)
    add_reason_lines(report_lines, score, odds)

else:
    report_lines.append("No Roughie Chance today")

conn.close()

report_text = "\n".join(report_lines)

print(report_text)

with open("golden_bullet_report.txt", "w") as file:
    file.write(report_text)

print("\nReport saved to golden_bullet_report.txt")