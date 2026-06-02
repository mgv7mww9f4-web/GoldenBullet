import sqlite3
import pandas as pd
import streamlit as st

DB_NAME = "goldenbullet.db"
MAX_SCORE = 116

st.set_page_config(
    page_title="Golden Bullet",
    page_icon="🏇",
    layout="wide"
)

st.title("🏇 Golden Bullet")
st.write("Paste race data below, import it, score it, and generate a report.")


def get_rating_percentage(score):
    return round((score / MAX_SCORE) * 100, 1)


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


def get_grade_score(grade):
    if grade is None:
        return 0

    grade = str(grade).upper()

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
    distance_range = str(distance_range).lower()

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
    track_condition = str(track_condition).lower()

    if "soft" in track_condition:
        return 8
    elif "good" in track_condition:
        return 6
    elif "heavy" in track_condition:
        return 5
    else:
        return 4


def safe_float(value):
    value = str(value).replace("$", "").replace("kg", "").strip()
    if value == "":
        return 0.0
    return float(value)


def safe_int(value):
    value = str(value).strip().lower()
    if value in ["", "x", "-"]:
        return 0
    return int(value)


def calculate_scores(df):
    scored_rows = []

    for _, row in df.iterrows():
        sky_rating_score = get_sky_rating_score(safe_int(row["sky_rating"]))
        form_score = get_form_score(
            safe_int(row["last_start_position"]),
            safe_int(row["second_last_position"]),
            safe_int(row["third_last_position"])
        )
        distance_score = get_distance_score(row["distance_range"])
        track_score = get_track_score(row["track_condition"])
        barrier_score = get_barrier_score(safe_int(row["barrier"]))
        jockey_score = 2
        trainer_score = 2
        grade_score = get_grade_score(row["grade"])
        weight_score = get_weight_score(safe_float(row["weight_carried"]))
        market_score = get_market_score(safe_float(row["odds"]))

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

        row_data = row.to_dict()
        row_data["score"] = total_score
        row_data["rating"] = get_rating_percentage(total_score)
        row_data["confidence"] = get_confidence(total_score)

        row_data["sky_rating_score"] = sky_rating_score
        row_data["form_score"] = form_score
        row_data["distance_score"] = distance_score
        row_data["track_score"] = track_score
        row_data["barrier_score"] = barrier_score
        row_data["jockey_score"] = jockey_score
        row_data["trainer_score"] = trainer_score
        row_data["grade_score"] = grade_score
        row_data["weight_score"] = weight_score
        row_data["market_score"] = market_score

        scored_rows.append(row_data)

    return pd.DataFrame(scored_rows)


def save_to_database(df):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("DROP TABLE IF EXISTS runners")

    df.to_sql("runners", conn, if_exists="replace", index=False)

    conn.commit()
    conn.close()


def get_bankroll():
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT current_bankroll FROM bankroll LIMIT 1")
        result = cursor.fetchone()
        conn.close()

        if result:
            return result[0]
    except:
        pass

    return 100


def get_stake(score, bankroll):
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


example_data = """horse_number,horse_name,race_number,grade,barrier,jockey,trainer,odds,last_start_position,second_last_position,third_last_position,distance_range,weight_carried,track_condition,weather,sky_rating
13,Zavega,6,BM58,1,Ben Looker,Alyssa and Troy Sweeney,3.50,1,3,1,800m-1000m,57,Soft 7,Fine,100
3,Irish Jig,6,BM58,8,Mikayla Weir,Scott Singleton,3.20,1,6,4,1200m-1280m,62,Soft 7,Fine,93
12,Dubalene,6,BM58,5,Luke Rolls,Colt Prosser,8.50,1,2,3,800m-1400m,57.5,Soft 7,Fine,80
"""

st.subheader("1. Paste Race Data")

race_data = st.text_area(
    "Paste CSV race data here",
    value=example_data,
    height=250
)

if st.button("Import and Score Race"):
    try:
        from io import StringIO

        df = pd.read_csv(StringIO(race_data))
        scored_df = calculate_scores(df)
        save_to_database(scored_df)

        st.success("Race imported and scored successfully!")

        bankroll = get_bankroll()

        st.subheader("Best Tip For Each Race")

        for race_number in sorted(scored_df["race_number"].unique()):
            race_df = scored_df[scored_df["race_number"] == race_number]
            best = race_df.sort_values("score", ascending=False).iloc[0]

            st.info(
                f"Race {race_number}: #{best['horse_number']} {best['horse_name']} | "
                f"Score {best['score']}/{MAX_SCORE} | "
                f"Rating {best['rating']}% | "
                f"Stake {get_stake(best['score'], bankroll)}"
            )

        st.subheader("Top 3 Chances")

        for race_number in sorted(scored_df["race_number"].unique()):
            st.write(f"Race {race_number}")
            race_df = scored_df[scored_df["race_number"] == race_number]
            top3 = race_df.sort_values("score", ascending=False).head(3)

            st.dataframe(
                top3[[
                    "horse_number",
                    "horse_name",
                    "odds",
                    "score",
                    "rating",
                    "confidence"
                ]]
            )

        st.subheader("Golden Bullet")

        golden = scored_df.sort_values("score", ascending=False).iloc[0]

        st.success(
            f"#{golden['horse_number']} {golden['horse_name']} | "
            f"Race {golden['race_number']} | "
            f"Odds ${golden['odds']} | "
            f"Score {golden['score']}/{MAX_SCORE} | "
            f"Rating {golden['rating']}% | "
            f"Confidence {golden['confidence']} | "
            f"Stake {get_stake(golden['score'], bankroll)}"
        )

        st.write("Score Breakdown")
        st.json({
            "Sky Rating": f"{golden['sky_rating_score']}/15",
            "Form": f"{golden['form_score']}/35",
            "Distance": f"{golden['distance_score']}/10",
            "Track": f"{golden['track_score']}/8",
            "Barrier": f"{golden['barrier_score']}/8",
            "Jockey": f"{golden['jockey_score']}/2",
            "Trainer": f"{golden['trainer_score']}/2",
            "Grade": f"{golden['grade_score']}/6",
            "Weight": f"{golden['weight_score']}/10",
            "Market": f"{golden['market_score']}/20"
        })

        st.subheader("Roughie Chance")

        roughies = scored_df[
            (scored_df["odds"].astype(float) >= 15)
            & (scored_df["score"].astype(float) >= 65)
        ]

        if len(roughies) > 0:
            roughie = roughies.sort_values("score", ascending=False).iloc[0]

            st.warning(
                f"#{roughie['horse_number']} {roughie['horse_name']} | "
                f"Race {roughie['race_number']} | "
                f"Odds ${roughie['odds']} | "
                f"Score {roughie['score']}/{MAX_SCORE} | "
                f"Rating {roughie['rating']}% | "
                f"Stake ${bankroll * 0.01:.2f} each-way"
            )
        else:
            st.write("No Roughie Chance found.")

    except Exception as error:
        st.error("Something went wrong.")
        st.write(error)