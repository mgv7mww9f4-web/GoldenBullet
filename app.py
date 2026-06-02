import re
import tempfile
import sqlite3
from io import StringIO

import pandas as pd
import streamlit as st
from PIL import Image
from rapidocr_onnxruntime import RapidOCR


DB_NAME = "goldenbullet.db"
MAX_SCORE = 116

st.set_page_config(
    page_title="Golden Bullet",
    page_icon="🏇",
    layout="wide"
)

st.title("🏇 Golden Bullet")
st.write("Upload screenshots, extract text, auto-build race data, then score the race.")


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

    try:
        return float(value)
    except:
        return 0.0


def safe_int(value):
    value = str(value).strip().lower()

    if value in ["", "x", "-"]:
        return 0

    try:
        return int(value)
    except:
        return 0


def extract_last_three_form_numbers(text):
    digits = re.findall(r"\d", text)

    if len(digits) >= 3:
        return int(digits[-1]), int(digits[-2]), int(digits[-3])

    if len(digits) == 2:
        return int(digits[-1]), int(digits[-2]), 0

    if len(digits) == 1:
        return int(digits[-1]), 0, 0

    return 0, 0, 0


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


def get_bankroll():
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT current_bankroll FROM bankroll LIMIT 1")
        result = cursor.fetchone()
        conn.close()

        if result:
            return result[0]
    except Exception:
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


def run_ocr(uploaded_files):
    engine = RapidOCR()
    all_text = []

    for uploaded_file in uploaded_files:
        image = Image.open(uploaded_file)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as temp_file:
            image.save(temp_file.name)
            result, _ = engine(temp_file.name)

        all_text.append(f"--- {uploaded_file.name} ---")

        if result:
            for line in result:
                text = line[1]
                all_text.append(text)

        all_text.append("")

    return "\n".join(all_text)


def build_csv_from_ocr(ocr_text):
    lines = [line.strip() for line in ocr_text.splitlines() if line.strip()]

    horse_rows = []

    current_number = None
    current_name = None
    current_odds = 0
    current_sky_rating = 0
    current_weight = 0
    current_barrier = 0
    current_form = ""

    race_number = 1
    grade = "BM58"
    track_condition = "Soft 7"
    weather = "Fine"
    distance_range = "1000m"

    for line in lines:
        lower = line.lower()

        race_match = re.search(r"race\s+(\d+)", lower)
        if race_match:
            race_number = int(race_match.group(1))

        if "bm" in lower:
            grade_match = re.search(r"(bm\d+)", lower)
            if grade_match:
                grade = grade_match.group(1).upper()

        if "soft" in lower:
            track_condition = "Soft 7"

        if "good" in lower:
            track_condition = "Good"

        odds_match = re.search(r"\$?(\d+\.\d+)", line)
        if odds_match:
            current_odds = float(odds_match.group(1))

        sky_match = re.search(r"sky\s*rating\s*(\d+)", lower)
        if sky_match:
            current_sky_rating = int(sky_match.group(1))

        weight_match = re.search(r"(\d+\.?\d*)\s*kg", lower)
        if weight_match:
            current_weight = float(weight_match.group(1))

        barrier_match = re.search(r"barrier\s*(\d+)", lower)
        if barrier_match:
            current_barrier = int(barrier_match.group(1))

        distance_match = re.search(r"(\d{3,4}m(?:-\d{3,4}m)?)", lower)
        if distance_match:
            distance_range = distance_match.group(1)

        form_match = re.search(r"\b[x\d]{3,6}\b", lower)
        if form_match:
            current_form = form_match.group(0)

        horse_match = re.match(r"^#?(\d+)\s+([A-Za-z][A-Za-z\s'\-]+)$", line)
        if horse_match:
            if current_number is not None and current_name is not None:
                last_start, second_last, third_last = extract_last_three_form_numbers(current_form)

                horse_rows.append([
                    current_number,
                    current_name,
                    race_number,
                    grade,
                    current_barrier,
                    "Unknown Jockey",
                    "Unknown Trainer",
                    current_odds,
                    last_start,
                    second_last,
                    third_last,
                    distance_range,
                    current_weight,
                    track_condition,
                    weather,
                    current_sky_rating
                ])

            current_number = int(horse_match.group(1))
            current_name = horse_match.group(2).strip()

            current_odds = 0
            current_sky_rating = 0
            current_weight = 0
            current_barrier = 0
            current_form = ""

    if current_number is not None and current_name is not None:
        last_start, second_last, third_last = extract_last_three_form_numbers(current_form)

        horse_rows.append([
            current_number,
            current_name,
            race_number,
            grade,
            current_barrier,
            "Unknown Jockey",
            "Unknown Trainer",
            current_odds,
            last_start,
            second_last,
            third_last,
            distance_range,
            current_weight,
            track_condition,
            weather,
            current_sky_rating
        ])

    header = "horse_number,horse_name,race_number,grade,barrier,jockey,trainer,odds,last_start_position,second_last_position,third_last_position,distance_range,weight_carried,track_condition,weather,sky_rating"

    csv_lines = [header]

    for row in horse_rows:
        csv_lines.append(",".join(str(item) for item in row))

    if len(csv_lines) == 1:
        return header + "\n"

    return "\n".join(csv_lines)


example_csv = """horse_number,horse_name,race_number,grade,barrier,jockey,trainer,odds,last_start_position,second_last_position,third_last_position,distance_range,weight_carried,track_condition,weather,sky_rating
13,Zavega,6,BM58,1,Ben Looker,Alyssa and Troy Sweeney,3.50,1,3,1,800m-1000m,57,Soft 7,Fine,100
3,Irish Jig,6,BM58,8,Mikayla Weir,Scott Singleton,3.20,1,6,4,1200m-1280m,62,Soft 7,Fine,93
12,Dubalene,6,BM58,5,Luke Rolls,Colt Prosser,8.50,1,2,3,800m-1400m,57.5,Soft 7,Fine,80
"""

st.subheader("1. Upload screenshots")

uploaded_files = st.file_uploader(
    "Upload Sportsbet/TAB screenshots",
    type=["png", "jpg", "jpeg"],
    accept_multiple_files=True
)

if uploaded_files:
    if st.button("Extract text and build CSV"):
        with st.spinner("Reading screenshots..."):
            ocr_text = run_ocr(uploaded_files)
            built_csv = build_csv_from_ocr(ocr_text)

            st.session_state["ocr_text"] = ocr_text
            st.session_state["race_csv"] = built_csv

if "ocr_text" in st.session_state:
    st.subheader("2. Extracted screenshot text")
    st.text_area(
        "OCR text",
        value=st.session_state["ocr_text"],
        height=250
    )

st.subheader("3. Race CSV")

default_csv = st.session_state.get("race_csv", example_csv)

race_data = st.text_area(
    "Check this data. Edit anything wrong before scoring.",
    value=default_csv,
    height=300
)

if st.button("Import and Score Race"):
    try:
        df = pd.read_csv(StringIO(race_data))
        scored_df = calculate_scores(df)

        bankroll = get_bankroll()

        st.success("Race scored successfully!")

        st.subheader("Best Tip For Each Race")

        for race_number in sorted(scored_df["race_number"].unique()):
            race_df = scored_df[scored_df["race_number"] == race_number]
            best = race_df.sort_values("score", ascending=False).iloc[0]

            st.info(
                f"Race {race_number}: #{best['horse_number']} {best['horse_name']} | "
                f"Score {best['score']}/{MAX_SCORE} | "
                f"Rating {best['rating']}% | "
                f"Confidence {best['confidence']} | "
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