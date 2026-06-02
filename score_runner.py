def get_grade_score(grade):
    if grade == "Grade 5":
        return 10
    elif grade == "Grade 4":
        return 8
    elif grade == "Grade 3":
        return 6
    elif grade == "Grade 2":
        return 4
    elif grade == "Grade 1":
        return 2
    else:
        return 0


def calculate_score(
    horse_number,
    horse_name,
    grade,
    form_score,
    distance_score,
    track_score,
    barrier_score,
    jockey_score,
    trainer_score,
    market_score
):
    grade_score = get_grade_score(grade)

    total = (
        form_score +
        distance_score +
        track_score +
        barrier_score +
        jockey_score +
        trainer_score +
        market_score +
        grade_score
    )

    print(f"#{horse_number} {horse_name}")
    print("Grade:", grade)
    print("Grade Score:", grade_score)
    print("Total Score:", total)

    return total


calculate_score(
    4,
    "Golden Lad",
    "Grade 5",
    22,
    14,
    15,
    8,
    9,
    9,
    10
)