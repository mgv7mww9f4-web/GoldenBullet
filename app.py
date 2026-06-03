import re
import tempfile
from io import StringIO

import pandas as pd
import streamlit as st
from PIL import Image

try:
    from rapidocr_onnxruntime import RapidOCR
    OCR_AVAILABLE = True
except Exception:
    OCR_AVAILABLE = False


MAX_SCORE = 116


st.set_page_config(
    page_title="Golden Bullet",
    page_icon="🏇",
    layout="wide"
)

st.title("🏇 Golden Bullet")
st.write("Upload meeting screenshots, create race lists, paste horse CSVs, and score races.")


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


def safe_float(value):
    value = str(value).replace("$", "").replace("kg", "").strip()

    if value == "":
        return 0.0

    try:
        return float(value)
    except Exception:
        return 0.0


def safe_int(value):
    value = str(value).strip().lower()

    if value in ["", "x", "-"]:
        return 0

    try:
        return int(value)
    except Exception:
        return 0


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
    if not OCR_AVAILABLE:
        return "OCR is not available. Check requirements.txt and Streamlit logs."

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
                all_text.append(line[1])

        all_text.append("")

    return "\n".join(all_text)


def parse_meetings(text):
    known_tracks = [
        "Sandown",
        "Warwick Farm",
        "WarwickFarm",
        "Doomben",
        "Moree",
        "Flemington",
        "Randwick",
        "Rosehill",
        "Caulfield",
        "Morphettville",
        "Eagle Farm",
        "Canterbury",
        "Geelong",
        "Ballarat",
        "Bendigo",
        "Belmont",
        "Ascot",
        "Murray Bridge",
        "Gawler"
    ]

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    meetings = {}

    for i, line in enumerate(lines):
        matched_track = None

        for track in known_tracks:
            if track.lower() in line.lower():
                matched_track = track
                break

        if matched_track:
            nearby_lines = lines[i:i + 6]
            nearby_text = " ".join(nearby_lines)

            times = re.findall(r"\b\d{1,2}:\d{2}\b", nearby_text)

            clean_times = []
            for time in times:
                if time not in clean_times:
                    clean_times.append(time)

            meetings[matched_track] = clean_times[:10]

    return meetings


example_csv = """horse_number,horse_name,race_number,grade,barrier,jockey,trainer,odds,last_start_position,second_last_position,third_last_position,distance_range,weight_carried,track_condition,weather,sky_rating
13,Zavega,6,BM58,1,Ben Looker,Alyssa and Troy Sweeney,3.50,1,3,1,800m-1000m,57,Soft 7,Fine,100
3,Irish Jig,6,BM58,8,Mikayla Weir,Scott Singleton,3.20,1,6,4,1200m-1280m,62,Soft 7,Fine,93
12,Dubalene,6,BM58,5,Luke Rolls,Colt Prosser,8.50,1,2,3,800m-1400m,57.5,Soft 7,Fine,80
"""


st.subheader("1. Upload today's meeting screenshot")

meeting_files = st.file_uploader(
    "Upload screenshot showing tracks and race times",
    type=["png", "jpg", "jpeg"],
    accept_multiple_files=True,
    key="meeting_uploader"
)

if meeting_files:
    if st.button("Read Meeting Screenshot"):
        with st.spinner("Reading meeting screenshot..."):
            ocr_text = run_ocr(meeting_files)
            meetings = parse_meetings(ocr_text)

            st.session_state["meeting_ocr_text"] = ocr_text
            st.session_state["meetings"] = meetings


if "meeting_ocr_text" in st.session_state:
    st.subheader("OCR Text")
    st.text_area(
        "Extracted meeting text",
        value=st.session_state["meeting_ocr_text"],
        height=200
    )


if "meetings" in st.session_state:
    st.subheader("2. Today's Meetings")

    meetings = st.session_state["meetings"]

    if len(meetings) == 0:
        st.warning("No meetings found. Add races manually below.")
    else:
        for track, times in meetings.items():
            st.write(f"### {track}")

            if len(times) == 0:
                st.write("No race times found.")
            else:
                race_data = []

                for index, time in enumerate(times, start=1):
                    race_data.append({
                        "Race": f"R{index}",
                        "Time": time,
                        "Status": "Ready for horse data"
                    })

                st.dataframe(pd.DataFrame(race_data), use_container_width=True)


st.subheader("3. Add Horse Data For A Race")

track_name = st.text_input("Track name", value="Sandown")
race_number = st.number_input("Race number", min_value=1, max_value=20, value=1)
race_time = st.text_input("Race time", value="11:55")
bankroll = st.number_input("Bankroll", min_value=1.0, value=150.0, step=1.0)

horse_csv = st.text_area(
    "Paste horse CSV here",
    value=example_csv,
    height=300
)


if st.button("Score Race"):
    try:
        df = pd.read_csv(StringIO(horse_csv))
        scored_df = calculate_scores(df)

        st.success(f"Race scored: {track_name} Race {race_number} at {race_time}")

        st.subheader("Best Tip")

        best = scored_df.sort_values("score", ascending=False).iloc[0]

        st.info(
            f"#{best['horse_number']} {best['horse_name']} | "
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

        st.subheader("Golden Bullet")

        st.success(
            f"#{best['horse_number']} {best['horse_name']} | "
            f"Odds ${best['odds']} | "
            f"Score {best['score']}/{MAX_SCORE} | "
            f"Rating {best['rating']}% | "
            f"Confidence {best['confidence']} | "
            f"Stake {get_stake(best['score'], bankroll)}"
        )

        st.write("Score Breakdown")
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

    except Exception as error:
        st.error("Something went wrong while scoring.")
        st.write(error)