import sqlite3


MAX_SCORE = 116


def get_grade_score(grade):
    if grade is None:
        return 0

    grade = grade.upper()

    if "BM58" in grade:
        return 6
    elif "BM64" in grade:
        return 5
    elif "BM70" in grade:
        return 4
    elif "MAIDEN" in grade:
        return 3
    elif "MDN" in grade:
        return 3
    else:
        return 3


def get_barrier_score(barrier):
    if barrier is None:
        return 0

    if 1 <= barrier <= 4:
        return 8
    elif 5 <= barrier <= 8:
        return 5
    else:
        return 2


def get_form_score(last_start, second_last, third_last):
    score = 0

    recent_runs = [
        (last_start, 20),
        (second_last, 10),
        (third_last, 5)
    ]

    for position, max_points in recent_runs:
        if position == 1:
            score += max_points
        elif position == 2:
            score += round(max_points * 0.8)
        elif position == 3:
            score += round(max_points * 0.6)
        elif 4 <= position <= 5:
            score += round(max_points * 0.3)
        elif position == 0:
            score += 0
        else:
            score += 0

    return min(score, 35)


def get_weight_score(weight_carried):
    if weight_carried <= 0:
        return 0
    elif weight_carried <= 55:
        return 10
    elif weight_carried <= 57:
        return 8
    elif weight_carried <= 59:
        return 5
    else:
        return 2


def get_market_score(odds):
    if odds <= 0:
        return 0
    elif odds <= 3:
        return 20
    elif odds <= 5:
        return 15
    elif odds <= 10:
        return 10
    elif odds <= 20:
        return 5
    elif odds <= 40:
        return 2
    else:
        return 0


def get_sky_rating_score(sky_rating):
    if sky_rating >= 95:
        return 15
    elif sky_rating >= 90:
        return 12
    elif sky_rating >= 85:
        return 10
    elif sky_rating >= 80:
        return 7
    elif sky_rating >= 70:
        return 4
    else:
        return 0


def get_distance_score(distance_range):
    if distance_range is None:
        return 0

    distance_range = distance_range.lower()

    if "1400" in distance_range:
        return 10
    elif "1300" in distance_range:
        return 8
    elif "1200" in distance_range:
        return 6
    elif "1000" in distance_range or "1100" in distance_range:
        return 5
    else:
        return 4


def get_track_score(track_condition):
    if track_condition is None:
        return 0

    track_condition = track_condition.lower()

    if "soft" in track_condition:
        return 8
    elif "good" in track_condition:
        return 6
    elif "heavy" in track_condition:
        return 5
    else:
        return 4


def get_jockey_score(jockey):
    return 2


def get_trainer_score(trainer):
    return 2


conn = sqlite3.connect("goldenbullet.db")
cursor = conn.cursor()

cursor.execute("""
SELECT id, horse_name, grade, barrier, jockey, trainer, odds,
       last_start_position, second_last_position, third_last_position,
       weight_carried, sky_rating, distance_range, track_condition
FROM runners
""")

runners = cursor.fetchall()

for runner in runners:
    (
        runner_id,
        horse_name,
        grade,
        barrier,
        jockey,
        trainer,
        odds,
        last_start,
        second_last,
        third_last,
        weight_carried,
        sky_rating,
        distance_range,
        track_condition
    ) = runner

    sky_rating_score = get_sky_rating_score(sky_rating)
    form_score = get_form_score(last_start, second_last, third_last)
    distance_score = get_distance_score(distance_range)
    track_score = get_track_score(track_condition)
    barrier_score = get_barrier_score(barrier)
    jockey_score = get_jockey_score(jockey)
    trainer_score = get_trainer_score(trainer)
    grade_score = get_grade_score(grade)
    weight_score = get_weight_score(weight_carried)
    market_score = get_market_score(odds)

    total_score = (
        sky_rating_score
        + form_score
        + distance_score
        + track_score
        + barrier_score
        + jockey_score
        + trainer_score
        + grade_score
        + weight_score
        + market_score
    )

    cursor.execute("""
    UPDATE runners
    SET sky_rating_score = ?,
        form_score = ?,
        distance_score = ?,
        track_score = ?,
        barrier_score = ?,
        jockey_score = ?,
        trainer_score = ?,
        grade_score = ?,
        weight_score = ?,
        market_score = ?,
        score = ?
    WHERE id = ?
    """, (
        sky_rating_score,
        form_score,
        distance_score,
        track_score,
        barrier_score,
        jockey_score,
        trainer_score,
        grade_score,
        weight_score,
        market_score,
        total_score,
        runner_id
    ))

    percentage = (total_score / MAX_SCORE) * 100
    print(f"{horse_name}: {total_score}/{MAX_SCORE} ({percentage:.1f}%)")

conn.commit()
conn.close()

print("All scores updated")