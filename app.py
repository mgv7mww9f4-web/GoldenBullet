from io import StringIO
from datetime import date

import pandas as pd
import requests
import streamlit as st

MAX_SCORE = 116

st.set_page_config(
    page_title="Golden Bullet",
    page_icon="🏇",
    layout="wide"
)

st.title("🏇 Golden Bullet")

try:
    FORMFAV_API_KEY = st.secrets["FORMFAV_API_KEY"]
    st.success(f"FormFav API Connected: {FORMFAV_API_KEY[:6]}...")
except Exception:
    FORMFAV_API_KEY = None
    st.error("FormFav API key not found in Streamlit Secrets.")


def safe_float(value):
    value = str(value).replace("$", "").replace("kg", "").strip()
    try:
        return float(value)
    except Exception:
        return 0.0


def safe_int(value):
    value = str(value).strip().lower()
    if value in ["", "x", "-", "nan", "none"]:
        return 0
    try:
        return int(float(value))
    except Exception:
        return 0


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


def get_weight_score(weight):
    if weight <= 0:
        return 0
    elif weight <= 55:
        return 10
    elif weight <= 57:
        return 8
    elif weight <= 59:
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


def get_sky_rating_score(rating):
    if rating >= 95:
        return 15
    elif rating >= 90:
        return 12
    elif rating >= 85:
        return 10
    elif rating >= 80:
        return 7
    elif rating >= 70:
        return 4
    else:
        return 0


def get_distance_score(distance):
    distance = str(distance).lower()

    if "1400" in distance:
        return 10
    elif "1300" in distance:
        return 8
    elif "1200" in distance:
        return 6
    elif "1000" in distance or "1100" in distance:
        return 5
    else:
        return 4


def get_track_score(track):
    track = str(track).lower()

    if "soft" in track:
        return 8
    elif "good" in track:
        return 6
    elif "heavy" in track:
        return 5
    else:
        return 4


def calculate_scores(df):
    scored_rows = []

    for _, row in df.iterrows():
        sky_rating_score = get_sky_rating_score(safe_int(row.get("sky_rating", 0)))

        form_score = get_form_score(
            safe_int(row.get("last_start_position", 0)),
            safe_int(row.get("second_last_position", 0)),
            safe_int(row.get("third_last_position", 0))
        )

        distance_score = get_distance_score(row.get("distance_range", ""))
        track_score = get_track_score(row.get("track_condition", ""))
        barrier_score = get_barrier_score(safe_int(row.get("barrier", 0)))
        jockey_score = 2
        trainer_score = 2
        grade_score = get_grade_score(row.get("grade", ""))
        weight_score = get_weight_score(safe_float(row.get("weight_carried", 0)))
        market_score = get_market_score(safe_float(row.get("odds", 0)))

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


def display_scored_race(scored_df, bankroll):
    if scored_df.empty:
        st.warning("No runners found.")
        return

    best = scored_df.sort_values("score", ascending=False).iloc[0]

    st.subheader("🏆 Golden Bullet")

    st.success(
        f"#{best['horse_number']} {best['horse_name']} | "
        f"Odds ${best['odds']} | "
        f"Score {best['score']}/{MAX_SCORE} | "
        f"Rating {best['rating']}% | "
        f"Confidence {best['confidence']} | "
        f"Stake {get_stake(best['score'], bankroll)}"
    )

    st.subheader("Top 3 Chances")

    top3 = scored_df.sort_values("score", ascending=False).head(3)

    st.dataframe(
        top3[[
            "horse_number",
            "horse_name",
            "odds",
            "score",
            "rating",
            "confidence"
        ]],
        use_container_width=True
    )

    st.subheader("Score Breakdown")

    st.json({
        "Sky Rating": f"{best['sky_rating_score']}/15",
        "Form": f"{best['form_score']}/35",
        "Distance": f"{best['distance_score']}/10",
        "Track": f"{best['track_score']}/8",
        "Barrier": f"{best['barrier_score']}/8",
        "Jockey": f"{best['jockey_score']}/2",
        "Trainer": f"{best['trainer_score']}/2",
        "Grade": f"{best['grade_score']}/6",
        "Weight": f"{best['weight_score']}/10",
        "Market": f"{best['market_score']}/20"
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
            f"Odds ${roughie['odds']} | "
            f"Score {roughie['score']}/{MAX_SCORE} | "
            f"Rating {roughie['rating']}% | "
            f"Stake ${bankroll * 0.01:.2f} each-way"
        )
    else:
        st.write("No Roughie Chance found.")


def call_formfav_form(race_date, track, race):
    url = "https://api.formfav.com/v1/form"

    headers = {
        "X-API-Key": FORMFAV_API_KEY,
        "Accept": "application/json"
    }

    params = {
        "date": race_date,
        "track": track,
        "race": race
    }

    response = requests.get(
        url,
        headers=headers,
        params=params,
        timeout=30
    )

    return response


def normalise_formfav_to_csv(data, race_number, track_condition):
    runners = []

    if isinstance(data, dict):
        if "data" in data and isinstance(data["data"], list):
            runners = data["data"]
        elif "runners" in data and isinstance(data["runners"], list):
            runners = data["runners"]
        elif "horses" in data and isinstance(data["horses"], list):
            runners = data["horses"]
        elif "race" in data and isinstance(data["race"], dict):
            race_data = data["race"]
            if "runners" in race_data:
                runners = race_data["runners"]
        else:
            runners = [data]

    elif isinstance(data, list):
        runners = data

    rows = []

    for index, runner in enumerate(runners, start=1):
        horse_number = (
            runner.get("number")
            or runner.get("horse_number")
            or runner.get("runner_number")
            or index
        )

        horse_name = (
            runner.get("horse")
            or runner.get("horse_name")
            or runner.get("name")
            or runner.get("runner_name")
            or "Unknown"
        )

        odds = (
            runner.get("odds")
            or runner.get("price")
            or runner.get("fixed_odds")
            or runner.get("win_odds")
            or 0
        )

        barrier = (
            runner.get("barrier")
            or runner.get("barrier_number")
            or runner.get("gate")
            or 0
        )

        jockey = (
            runner.get("jockey")
            or runner.get("jockey_name")
            or "Unknown"
        )

        trainer = (
            runner.get("trainer")
            or runner.get("trainer_name")
            or "Unknown"
        )

        weight = (
            runner.get("weight")
            or runner.get("weight_carried")
            or runner.get("allocated_weight")
            or 0
        )

        rating = (
            runner.get("rating")
            or runner.get("form_rating")
            or runner.get("score")
            or runner.get("prediction_score")
            or 0
        )

        distance = (
            runner.get("distance")
            or runner.get("distance_range")
            or "Unknown"
        )

        grade = (
            runner.get("grade")
            or runner.get("class")
            or runner.get("race_class")
            or "API"
        )

        form = str(
            runner.get("form")
            or runner.get("last_10")
            or runner.get("recent_form")
            or ""
        )

        form_digits = [int(char) for char in form if char.isdigit()]

        if len(form_digits) >= 3:
            last_start = form_digits[-1]
            second_last = form_digits[-2]
            third_last = form_digits[-3]
        elif len(form_digits) == 2:
            last_start = form_digits[-1]
            second_last = form_digits[-2]
            third_last = 0
        elif len(form_digits) == 1:
            last_start = form_digits[-1]
            second_last = 0
            third_last = 0
        else:
            last_start = 0
            second_last = 0
            third_last = 0

        rows.append({
            "horse_number": horse_number,
            "horse_name": horse_name,
            "race_number": race_number,
            "grade": grade,
            "barrier": barrier,
            "jockey": jockey,
            "trainer": trainer,
            "odds": odds,
            "last_start_position": last_start,
            "second_last_position": second_last,
            "third_last_position": third_last,
            "distance_range": distance,
            "weight_carried": weight,
            "track_condition": track_condition,
            "weather": "Unknown",
            "sky_rating": rating
        })

    return pd.DataFrame(rows)


st.write("Use FormFav to load race form, or paste CSV manually.")

bankroll = st.number_input("Bankroll", min_value=1.0, value=150.0, step=1.0)

tab1, tab2 = st.tabs(["FormFav Race Loader", "Manual CSV Scorer"])

with tab1:
    st.subheader("FormFav Race Loader")

    if FORMFAV_API_KEY is None:
        st.error("Add FORMFAV_API_KEY to Streamlit Secrets first.")
    else:
        race_date = st.date_input("Race date", value=date.today())
        track = st.text_input("Track", value="Sandown")
        race = st.number_input("Race number", min_value=1, max_value=20, value=1)
        track_condition = st.text_input("Track condition", value="Unknown")

        if st.button("Load FormFav Race"):
            try:
                response = call_formfav_form(
                    race_date=str(race_date),
                    track=track,
                    race=int(race)
                )

                st.write("Status code:", response.status_code)
                st.write("URL:", response.url)

                data = response.json()

                if response.status_code != 200:
                    st.error("FormFav returned an error.")
                    st.json(data)
                else:
                    st.success("FormFav race loaded.")

                    st.subheader("Raw JSON")
                    st.json(data)

                    df = normalise_formfav_to_csv(
                        data=data,
                        race_number=int(race),
                        track_condition=track_condition
                    )

                    st.subheader("Generated Golden Bullet CSV")

                    csv_text = df.to_csv(index=False)

                    edited_csv = st.text_area(
                        "Check/edit before scoring",
                        value=csv_text,
                        height=300
                    )

                    if st.button("Score FormFav Race"):
                        edited_df = pd.read_csv(StringIO(edited_csv))
                        scored_df = calculate_scores(edited_df)
                        display_scored_race(scored_df, bankroll)

            except Exception as error:
                st.error("Could not load FormFav race.")
                st.write(error)


with tab2:
    st.subheader("Manual CSV Scorer")

    example_csv = """horse_number,horse_name,race_number,grade,barrier,jockey,trainer,odds,last_start_position,second_last_position,third_last_position,distance_range,weight_carried,track_condition,weather,sky_rating
13,Zavega,6,BM58,1,Ben Looker,Alyssa and Troy Sweeney,3.50,1,3,1,800m-1000m,57,Soft 7,Fine,100
3,Irish Jig,6,BM58,8,Mikayla Weir,Scott Singleton,3.20,1,6,4,1200m-1280m,62,Soft 7,Fine,93
12,Dubalene,6,BM58,5,Luke Rolls,Colt Prosser,8.50,1,2,3,800m-1400m,57.5,Soft 7,Fine,80
"""

    horse_csv = st.text_area(
        "Paste horse CSV here",
        value=example_csv,
        height=300
    )

    if st.button("Score Manual CSV"):
        try:
            df = pd.read_csv(StringIO(horse_csv))
            scored_df = calculate_scores(df)
            display_scored_race(scored_df, bankroll)

        except Exception as error:
            st.error("Something went wrong while scoring.")
            st.write(error)