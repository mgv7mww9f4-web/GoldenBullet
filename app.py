from io import StringIO
from datetime import date
import os

import pandas as pd
import requests
import streamlit as st

MAX_SCORE = 131
RACE_HISTORY_FILE = "race_history.csv"
SELECTION_HISTORY_FILE = "selection_history.csv"

st.set_page_config(page_title="Golden Bullet", page_icon="🏇", layout="wide")
st.title("🏇 Golden Bullet")

try:
    FORMFAV_API_KEY = st.secrets["FORMFAV_API_KEY"]
    st.success(f"FormFav API Connected: {FORMFAV_API_KEY[:6]}...")
except Exception:
    FORMFAV_API_KEY = None
    st.error("FormFav API key not found in Streamlit Secrets.")


def safe_float(value):
    try:
        return float(str(value).replace("$", "").replace("kg", "").strip())
    except Exception:
        return 0.0


def safe_int(value):
    try:
        return int(float(str(value).strip()))
    except Exception:
        return 0


def get_rating_percentage(score):
    return round((safe_float(score) / MAX_SCORE) * 100, 1)


def get_confidence(score):
    score = safe_float(score)

    if score >= 90:
        return "Elite"
    if score >= 80:
        return "High"
    if score >= 70:
        return "Medium"
    if score >= 65:
        return "Watch"
    return "Low"


def get_grade_score(grade):
    grade = str(grade).upper()

    if "BM58" in grade:
        return 6
    if "BM64" in grade:
        return 5
    if "BM70" in grade:
        return 4
    if "MAIDEN" in grade or "MDN" in grade:
        return 3
    return 3


def get_barrier_score(barrier):
    barrier = safe_int(barrier)

    if 1 <= barrier <= 4:
        return 8
    if 5 <= barrier <= 8:
        return 5
    return 2


def get_form_score(last_start, second_last, third_last):
    score = 0

    recent_runs = [
        (last_start, 20),
        (second_last, 10),
        (third_last, 5)
    ]

    for position, max_points in recent_runs:
        position = safe_int(position)

        if position == 1:
            score += max_points
        elif position == 2:
            score += round(max_points * 0.8)
        elif position == 3:
            score += round(max_points * 0.6)
        elif 4 <= position <= 5:
            score += round(max_points * 0.3)

    return min(score, 35)


def get_class_form_score(form_score, class_movement):
    class_movement = str(class_movement).upper().strip()
    good_form = safe_float(form_score) >= 20

    if good_form and class_movement == "W":
        return 15
    if good_form and class_movement == "E":
        return 7.5
    if good_form and class_movement == "S":
        return 5
    if not good_form and class_movement == "W":
        return 5
    if not good_form and class_movement == "E":
        return 3
    if not good_form and class_movement == "S":
        return 0

    return 3


def get_weight_score(weight):
    weight = safe_float(weight)

    if weight <= 0:
        return 0
    if weight <= 55:
        return 10
    if weight <= 57:
        return 8
    if weight <= 59:
        return 5
    return 2


def get_market_score(odds):
    odds = safe_float(odds)

    if odds <= 0:
        return 0
    if odds <= 3:
        return 20
    if odds <= 5:
        return 15
    if odds <= 10:
        return 10
    if odds <= 20:
        return 5
    if odds <= 40:
        return 2
    return 0


def get_sky_rating_score(rating):
    rating = safe_int(rating)

    if rating >= 95:
        return 15
    if rating >= 90:
        return 12
    if rating >= 85:
        return 10
    if rating >= 80:
        return 7
    if rating >= 70:
        return 4
    return 0


def get_distance_score(distance):
    distance = str(distance).lower()

    if "1400" in distance:
        return 10
    if "1300" in distance:
        return 8
    if "1200" in distance:
        return 6
    if "1000" in distance or "1100" in distance:
        return 5
    return 4


def get_track_score(track):
    track = str(track).lower()

    if "soft" in track:
        return 8
    if "good" in track:
        return 6
    if "heavy" in track:
        return 5
    return 4


def calculate_scores(df):
    scored_rows = []

    for _, row in df.iterrows():
        sky_rating_score = get_sky_rating_score(row.get("sky_rating", 0))

        form_score = get_form_score(
            row.get("last_start_position", 0),
            row.get("second_last_position", 0),
            row.get("third_last_position", 0)
        )

        class_form_score = get_class_form_score(
            form_score,
            row.get("class_movement", "E")
        )

        distance_score = get_distance_score(row.get("distance_range", ""))
        track_score = get_track_score(row.get("track_condition", ""))
        barrier_score = get_barrier_score(row.get("barrier", 0))
        jockey_score = 2
        trainer_score = 2
        grade_score = get_grade_score(row.get("grade", ""))
        weight_score = get_weight_score(row.get("weight_carried", 0))
        market_score = get_market_score(row.get("odds", 0))

        total_score = (
            sky_rating_score
            + form_score
            + class_form_score
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
        row_data["class_form_score"] = class_form_score
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
    score = safe_float(score)

    if score >= 90:
        stake = bankroll * 0.05
    elif score >= 80:
        stake = bankroll * 0.04
    elif score >= 70:
        stake = bankroll * 0.03
    else:
        stake = 0

    return round(stake, 2)


def call_formfav_form(race_date, track, race):
    url = "https://api.formfav.com/v1/form"

    headers = {
        "X-API-Key": FORMFAV_API_KEY,
        "Accept": "application/json"
    }

    params = {
        "date": str(race_date),
        "track": track,
        "race": int(race)
    }

    return requests.get(url, headers=headers, params=params, timeout=30)


def find_runners(data):
    if isinstance(data, list):
        return data

    if not isinstance(data, dict):
        return []

    if "runners" in data and isinstance(data["runners"], list):
        return data["runners"]

    for value in data.values():
        if isinstance(value, dict):
            runners = find_runners(value)
            if runners:
                return runners

    return []


def get_value(runner, keys, default=""):
    for key in keys:
        if key in runner and runner[key] not in [None, ""]:
            return runner[key]

    return default


def get_recent_form_positions(form):
    digits = [int(char) for char in str(form) if char.isdigit()]

    if len(digits) >= 3:
        return digits[-1], digits[-2], digits[-3]
    if len(digits) == 2:
        return digits[-1], digits[-2], 0
    if len(digits) == 1:
        return digits[-1], 0, 0

    return 0, 0, 0


def get_rating_from_runner(runner):
    stats = runner.get("stats", {})

    if isinstance(stats, dict):
        overall = stats.get("overall", {})

        if isinstance(overall, dict):
            place_percent = safe_float(overall.get("placePercent", 0))
            win_percent = safe_float(overall.get("winPercent", 0))
            return round((place_percent * 70) + (win_percent * 30))

    return 0


def normalise_formfav_to_df(data, race_number):
    runners = find_runners(data)

    race_distance = data.get("distance", "Unknown") if isinstance(data, dict) else "Unknown"
    race_condition = data.get("condition", "Unknown") if isinstance(data, dict) else "Unknown"
    race_weather = data.get("weather", "Unknown") if isinstance(data, dict) else "Unknown"
    race_class = data.get("raceClass", "API") if isinstance(data, dict) else "API"

    rows = []

    for index, runner in enumerate(runners, start=1):
        if not isinstance(runner, dict):
            continue

        if runner.get("scratched") is True:
            continue

        form = get_value(runner, ["form", "last20Starts"], "")
        last_start, second_last, third_last = get_recent_form_positions(form)

        rows.append({
            "horse_number": get_value(runner, ["number"], index),
            "horse_name": get_value(runner, ["name"], "Unknown"),
            "race_number": race_number,
            "grade": race_class,
            "barrier": get_value(runner, ["barrier"], 0),
            "jockey": get_value(runner, ["jockey"], "Unknown"),
            "trainer": get_value(runner, ["trainer"], "Unknown"),
            "odds": 0,
            "last_start_position": last_start,
            "second_last_position": second_last,
            "third_last_position": third_last,
            "distance_range": race_distance,
            "weight_carried": get_value(runner, ["weight"], 0),
            "track_condition": race_condition,
            "weather": race_weather,
            "sky_rating": get_rating_from_runner(runner),
            "class_movement": "E"
        })

    return pd.DataFrame(rows)


def apply_odds_and_class_to_df(df, odds_text):
    odds_map = {}
    class_map = {}

    for line in odds_text.strip().splitlines():
        parts = line.strip().split(",")

        if len(parts) >= 2:
            horse_number = safe_int(parts[0])
            odds = safe_float(parts[1])
            odds_map[horse_number] = odds

        if len(parts) >= 3:
            class_movement = str(parts[2]).upper().strip()
            if class_movement in ["W", "E", "S"]:
                class_map[horse_number] = class_movement

    df = df.copy()

    df["odds"] = df["horse_number"].apply(
        lambda horse_number: odds_map.get(safe_int(horse_number), 0)
    )

    df["class_movement"] = df["horse_number"].apply(
        lambda horse_number: class_map.get(safe_int(horse_number), "E")
    )

    return df


def build_odds_template(df):
    lines = []

    for _, row in df.iterrows():
        lines.append(f"{row['horse_number']},0,E")

    return "\n".join(lines)


def ensure_selection_columns(df):
    columns = [
        "race_id", "date", "track", "race_number", "pick_type",
        "horse_number", "horse_name", "odds", "score", "rating",
        "confidence", "stake", "finish_position", "result", "profit_loss"
    ]

    for column in columns:
        if column not in df.columns:
            df[column] = ""

    df = df[columns]

    df["race_id"] = df["race_id"].astype(str)
    df["date"] = df["date"].astype(str)
    df["track"] = df["track"].astype(str)
    df["race_number"] = df["race_number"].astype(str)
    df["pick_type"] = df["pick_type"].astype(str)
    df["horse_number"] = df["horse_number"].astype(str)
    df["horse_name"] = df["horse_name"].astype(str)
    df["odds"] = df["odds"].apply(safe_float)
    df["score"] = df["score"].apply(safe_float)
    df["rating"] = df["rating"].apply(safe_float)
    df["confidence"] = df["confidence"].astype(str)
    df["stake"] = df["stake"].apply(safe_float)
    df["finish_position"] = df["finish_position"].astype(str)
    df["result"] = df["result"].astype(str)
    df["profit_loss"] = df["profit_loss"].apply(safe_float)

    return df


def ensure_race_columns(df):
    columns = [
        "race_id", "date", "track", "race_number", "horse_number",
        "horse_name", "odds", "score", "rating", "confidence",
        "finish_position"
    ]

    for column in columns:
        if column not in df.columns:
            df[column] = ""

    df = df[columns]

    df["race_id"] = df["race_id"].astype(str)
    df["date"] = df["date"].astype(str)
    df["track"] = df["track"].astype(str)
    df["race_number"] = df["race_number"].astype(str)
    df["horse_number"] = df["horse_number"].astype(str)
    df["horse_name"] = df["horse_name"].astype(str)
    df["odds"] = df["odds"].apply(safe_float)
    df["score"] = df["score"].apply(safe_float)
    df["rating"] = df["rating"].apply(safe_float)
    df["confidence"] = df["confidence"].astype(str)
    df["finish_position"] = df["finish_position"].astype(str)

    return df


def load_race_history():
    if os.path.exists(RACE_HISTORY_FILE):
        return ensure_race_columns(pd.read_csv(RACE_HISTORY_FILE, dtype=str))

    return ensure_race_columns(pd.DataFrame())


def save_race_history(df):
    df = ensure_race_columns(df)
    df.to_csv(RACE_HISTORY_FILE, index=False)


def load_selection_history():
    if os.path.exists(SELECTION_HISTORY_FILE):
        return ensure_selection_columns(pd.read_csv(SELECTION_HISTORY_FILE, dtype=str))

    return ensure_selection_columns(pd.DataFrame())


def save_selection_history(df):
    df = ensure_selection_columns(df)
    df.to_csv(SELECTION_HISTORY_FILE, index=False)


def build_race_id(race_date, track, race_number):
    clean_track = str(track).strip().lower().replace(" ", "_")
    return f"{race_date}_{clean_track}_R{race_number}"


def save_full_race_card(race_date, track, race_number, scored_df, bankroll):
    race_id = build_race_id(race_date, track, race_number)

    race_history = load_race_history()
    race_history = race_history[race_history["race_id"] != race_id]

    race_rows = []

    for _, row in scored_df.iterrows():
        race_rows.append({
            "race_id": race_id,
            "date": str(race_date),
            "track": str(track),
            "race_number": str(race_number),
            "horse_number": str(row["horse_number"]),
            "horse_name": str(row["horse_name"]),
            "odds": safe_float(row["odds"]),
            "score": safe_float(row["score"]),
            "rating": safe_float(row["rating"]),
            "confidence": str(row["confidence"]),
            "finish_position": ""
        })

    race_history = pd.concat([race_history, pd.DataFrame(race_rows)], ignore_index=True)
    save_race_history(race_history)

    selection_history = load_selection_history()
    selection_history = selection_history[selection_history["race_id"] != race_id]

    sorted_df = scored_df.sort_values("score", ascending=False)
    selections = []

    golden = sorted_df.iloc[0]
    selections.append(("Golden Bullet", golden, get_stake(golden["score"], bankroll)))

    for _, row in sorted_df.iloc[1:4].iterrows():
        selections.append(("Best Tip", row, get_stake(row["score"], bankroll)))

    roughies = scored_df[
        (scored_df["odds"].astype(float) >= 15)
        & (scored_df["score"].astype(float) >= 75)
    ]

    if len(roughies) > 0:
        roughie = roughies.sort_values("score", ascending=False).iloc[0]
        selections.append(("Roughie Chance", roughie, round(bankroll * 0.01, 2)))

    selection_rows = []

    for pick_type, row, stake in selections:
        selection_rows.append({
            "race_id": race_id,
            "date": str(race_date),
            "track": str(track),
            "race_number": str(race_number),
            "pick_type": str(pick_type),
            "horse_number": str(row["horse_number"]),
            "horse_name": str(row["horse_name"]),
            "odds": safe_float(row["odds"]),
            "score": safe_float(row["score"]),
            "rating": safe_float(row["rating"]),
            "confidence": str(row["confidence"]),
            "stake": safe_float(stake),
            "finish_position": "",
            "result": "Pending",
            "profit_loss": 0.0
        })

    selection_history = pd.concat([selection_history, pd.DataFrame(selection_rows)], ignore_index=True)
    save_selection_history(selection_history)


def calculate_profit_loss(stake, odds, finish_position):
    stake = safe_float(stake)
    odds = safe_float(odds)
    finish_position = safe_int(finish_position)

    if stake <= 0:
        return 0.0, "No Bet"

    if finish_position == 1:
        profit = (stake * odds) - stake
        return round(float(profit), 2), "Win"

    return round(float(-stake), 2), "Loss"


def update_results_for_race(race_id, first, second, third):
    placing_map = {
        safe_int(first): "1",
        safe_int(second): "2",
        safe_int(third): "3"
    }

    race_history = load_race_history()

    for index, row in race_history.iterrows():
        if str(row["race_id"]) == str(race_id):
            horse_number = safe_int(row["horse_number"])
            race_history.at[index, "finish_position"] = placing_map.get(horse_number, "99")

    save_race_history(race_history)

    selection_history = load_selection_history()

    for index, row in selection_history.iterrows():
        if str(row["race_id"]) == str(race_id):
            horse_number = safe_int(row["horse_number"])
            finish_position = placing_map.get(horse_number, "99")

            profit_loss, result = calculate_profit_loss(
                row["stake"],
                row["odds"],
                finish_position
            )

            selection_history.at[index, "finish_position"] = str(finish_position)
            selection_history.at[index, "result"] = str(result)
            selection_history.at[index, "profit_loss"] = float(profit_loss)

    save_selection_history(selection_history)


def display_scored_race(scored_df, bankroll, race_date, track, race_number):
    if scored_df.empty:
        st.warning("No runners found.")
        return

    save_full_race_card(race_date, track, race_number, scored_df, bankroll)

    sorted_df = scored_df.sort_values("score", ascending=False)
    best = sorted_df.iloc[0]
    best_stake = get_stake(best["score"], bankroll)

    st.success("Race card and selections saved automatically.")

    st.subheader("🏆 Golden Bullet")
    st.success(
        f"#{best['horse_number']} {best['horse_name']} | "
        f"Odds ${best['odds']} | "
        f"Score {best['score']}/{MAX_SCORE} | "
        f"Rating {best['rating']}% | "
        f"Confidence {best['confidence']} | "
        f"Stake ${best_stake:.2f} win"
    )

    st.subheader("Top 3 Chances")
    st.dataframe(
        sorted_df.head(3)[[
            "horse_number", "horse_name", "odds", "class_movement",
            "score", "rating", "confidence"
        ]],
        use_container_width=True
    )

    st.subheader("Score Breakdown")
    st.json({
        "Sky Rating": f"{best['sky_rating_score']}/15",
        "Form": f"{best['form_score']}/35",
        "Class + Form": f"{best['class_form_score']}/15",
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
        & (scored_df["score"].astype(float) >= 75)
    ]

    if len(roughies) > 0:
        roughie = roughies.sort_values("score", ascending=False).iloc[0]
        roughie_stake = round(bankroll * 0.01, 2)

        st.warning(
            f"#{roughie['horse_number']} {roughie['horse_name']} | "
            f"Odds ${roughie['odds']} | "
            f"Score {roughie['score']}/{MAX_SCORE} | "
            f"Rating {roughie['rating']}% | "
            f"Stake ${roughie_stake:.2f} each-way"
        )
    else:
        st.write("No Roughie Chance found.")


def show_group_roi(completed, group_column, title):
    st.subheader(title)

    if completed.empty:
        st.write("No completed results yet.")
        return

    stats = completed.groupby(group_column).agg(
        selections=(group_column, "count"),
        total_staked=("stake", "sum"),
        profit_loss=("profit_loss", "sum")
    ).reset_index()

    stats["roi"] = stats.apply(
        lambda row: round((row["profit_loss"] / row["total_staked"]) * 100, 1)
        if row["total_staked"] > 0 else 0,
        axis=1
    )

    st.dataframe(stats, use_container_width=True)


def show_results_tracker():
    race_history = load_race_history()
    selection_history = load_selection_history()

    if selection_history.empty:
        st.info("No saved races yet.")
        return

    completed = selection_history[selection_history["result"] != "Pending"]

    total_selections = len(selection_history)
    total_completed = len(completed)
    wins = len(completed[completed["result"] == "Win"])
    places = len(completed[completed["finish_position"].isin(["1", "2", "3"])])

    total_staked = completed["stake"].sum() if total_completed > 0 else 0
    profit_loss = completed["profit_loss"].sum() if total_completed > 0 else 0

    win_rate = (wins / total_completed * 100) if total_completed > 0 else 0
    place_rate = (places / total_completed * 100) if total_completed > 0 else 0
    roi = (profit_loss / total_staked * 100) if total_staked > 0 else 0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Selections", total_selections)
    col2.metric("Completed", total_completed)
    col3.metric("Win Rate", f"{win_rate:.1f}%")
    col4.metric("Place Rate", f"{place_rate:.1f}%")

    col5, col6, col7 = st.columns(3)
    col5.metric("Total Staked", f"${total_staked:.2f}")
    col6.metric("Profit/Loss", f"${profit_loss:.2f}")
    col7.metric("ROI", f"{roi:.1f}%")

    st.subheader("Enter Race Result")

    race_options_df = race_history[[
        "race_id", "date", "track", "race_number"
    ]].drop_duplicates()

    if not race_options_df.empty:
        options = {}

        for _, row in race_options_df.iterrows():
            label = f"{row['date']} {row['track']} R{row['race_number']}"
            options[label] = row["race_id"]

        selected_label = st.selectbox("Select race", list(options.keys()))
        selected_race_id = options[selected_label]

        first = st.number_input("1st horse number", min_value=1, max_value=30, value=1)
        second = st.number_input("2nd horse number", min_value=1, max_value=30, value=2)
        third = st.number_input("3rd horse number", min_value=1, max_value=30, value=3)

        if st.button("Save Race Result"):
            update_results_for_race(selected_race_id, first, second, third)
            st.success("Race result saved. Refresh the app to update stats.")

    show_group_roi(completed, "pick_type", "ROI By Pick Type")
    show_group_roi(completed, "confidence", "ROI By Confidence")

    if not completed.empty:
        completed_copy = completed.copy()
        completed_copy["score_range"] = pd.cut(
            completed_copy["score"],
            bins=[0, 65, 70, 80, 90, 200],
            labels=["Under 65", "65-69", "70-79", "80-89", "90+"]
        )
        show_group_roi(completed_copy, "score_range", "ROI By Score Range")

    st.subheader("Selection History")
    st.dataframe(selection_history, use_container_width=True)

    st.subheader("Full Race Card History")
    st.dataframe(race_history, use_container_width=True)


st.write("Load runners from FormFav, paste odds and W/E/S class movement, score races, and track results.")

bankroll = st.number_input("Bankroll", min_value=1.0, value=150.0, step=1.0)

tab1, tab2, tab3 = st.tabs([
    "FormFav + Manual Odds",
    "Manual CSV Scorer",
    "Results Tracker"
])

with tab1:
    st.subheader("FormFav + Manual Odds")

    if FORMFAV_API_KEY is None:
        st.error("Add FORMFAV_API_KEY to Streamlit Secrets first.")
    else:
        race_date = st.date_input("Race date", value=date.today())
        track = st.text_input("Track", value="Geelong")
        race = st.number_input("Race number", min_value=1, max_value=20, value=2)

        if st.button("Load FormFav Runners"):
            try:
                response = call_formfav_form(race_date, track, race)
                data = response.json()

                if response.status_code != 200:
                    st.error("FormFav returned an error.")
                    st.json(data)
                else:
                    df = normalise_formfav_to_df(data, int(race))

                    if df.empty:
                        st.warning("No runners found.")
                    else:
                        st.session_state["formfav_df"] = df
                        st.session_state["odds_template"] = build_odds_template(df)
                        st.success("Runners loaded from FormFav.")

            except Exception as error:
                st.error("Could not load FormFav race.")
                st.write(error)

    if "formfav_df" in st.session_state:
        st.subheader("Loaded Runners")
        st.dataframe(st.session_state["formfav_df"], use_container_width=True)

        st.subheader("Paste Odds + Class Movement")
        st.write("Format: horse number, odds, class movement")
        st.write("W = weaker, E = equal, S = stronger")
        st.code("1,8.50,W\n2,4.20,E\n3,12.00,S")

        odds_text = st.text_area(
            "Odds and Class Movement",
            value=st.session_state.get("odds_template", ""),
            height=250
        )

        if st.button("Apply Odds And Score"):
            try:
                df_with_odds = apply_odds_and_class_to_df(
                    st.session_state["formfav_df"],
                    odds_text
                )

                scored_df = calculate_scores(df_with_odds)
                display_scored_race(
                    scored_df,
                    bankroll,
                    race_date,
                    track,
                    int(race)
                )

            except Exception as error:
                st.error("Could not apply odds and score.")
                st.write(error)


with tab2:
    st.subheader("Manual CSV Scorer")

    example_csv = """horse_number,horse_name,race_number,grade,barrier,jockey,trainer,odds,last_start_position,second_last_position,third_last_position,distance_range,weight_carried,track_condition,weather,sky_rating,class_movement
13,Zavega,6,BM58,1,Ben Looker,Alyssa and Troy Sweeney,3.50,1,3,1,800m-1000m,57,Soft 7,Fine,100,W
3,Irish Jig,6,BM58,8,Mikayla Weir,Scott Singleton,3.20,1,6,4,1200m-1280m,62,Soft 7,Fine,93,E
12,Dubalene,6,BM58,5,Luke Rolls,Colt Prosser,8.50,1,2,3,800m-1400m,57.5,Soft 7,Fine,80,S
"""

    manual_date = st.date_input("Manual race date", value=date.today())
    manual_track = st.text_input("Manual track", value="Manual Track")
    manual_race = st.number_input("Manual race number", min_value=1, max_value=20, value=1)

    horse_csv = st.text_area(
        "Paste horse CSV here",
        value=example_csv,
        height=300
    )

    if st.button("Score Manual CSV"):
        try:
            df = pd.read_csv(StringIO(horse_csv))
            scored_df = calculate_scores(df)
            display_scored_race(
                scored_df,
                bankroll,
                manual_date,
                manual_track,
                int(manual_race)
            )

        except Exception as error:
            st.error("Something went wrong while scoring.")
            st.write(error)


with tab3:
    st.subheader("Results Tracker")
    show_results_tracker()