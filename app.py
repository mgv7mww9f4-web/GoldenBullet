import re
import tempfile
from PIL import Image

import pandas as pd
import streamlit as st
from rapidocr_onnxruntime import RapidOCR


st.set_page_config(
    page_title="Golden Bullet",
    page_icon="🏇",
    layout="wide"
)

st.title("🏇 Golden Bullet")
st.write("Upload today's race meeting screenshot, then add horse data under each race.")


def run_ocr(uploaded_files):
    engine = RapidOCR()
    all_text = []

    for uploaded_file in uploaded_files:
        image = Image.open(uploaded_file)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as temp_file:
            image.save(temp_file.name)
            result, _ = engine(temp_file.name)

        if result:
            for line in result:
                all_text.append(line[1])

    return "\n".join(all_text)


def parse_meetings(text):
    known_tracks = [
        "Sandown",
        "Warwick Farm",
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
        "Bendigo"
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
            meetings[matched_track] = []

            # Look only at the next few lines after the track name
            nearby_lines = lines[i:i + 8]
            nearby_text = " ".join(nearby_lines)

            times = re.findall(r"\b\d{1,2}:\d{2}\b", nearby_text)

            # Remove duplicate times while keeping order
            clean_times = []
            for time in times:
                if time not in clean_times:
                    clean_times.append(time)

            meetings[matched_track] = clean_times[:10]

    return meetings
    ]

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    meetings = {}

    current_track = None

    for line in lines:
        for track in known_tracks:
            if track.lower() in line.lower():
                current_track = track
                meetings[current_track] = []

        times = re.findall(r"\b\d{1,2}:\d{2}\b", line)

        if current_track and times:
            for time in times:
                meetings[current_track].append(time)

    return meetings


st.subheader("1. Upload today's race meetings screenshot")

meeting_files = st.file_uploader(
    "Upload screenshot showing tracks and race times",
    type=["png", "jpg", "jpeg"],
    accept_multiple_files=True
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
        st.warning("No meetings found. You can still add races manually below.")
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

st.subheader("3. Select Race To Add Horse Data")

track_name = st.text_input("Track name", value="Sandown")
race_number = st.number_input("Race number", min_value=1, max_value=20, value=1)
race_time = st.text_input("Race time", value="11:55")

st.write("Paste horse CSV for this race below.")

example_csv = """horse_number,horse_name,race_number,grade,barrier,jockey,trainer,odds,last_start_position,second_last_position,third_last_position,distance_range,weight_carried,track_condition,weather,sky_rating
13,Zavega,6,BM58,1,Ben Looker,Alyssa and Troy Sweeney,3.50,1,3,1,800m-1000m,57,Soft 7,Fine,100
"""

horse_csv = st.text_area(
    "Horse CSV",
    value=example_csv,
    height=250
)

if st.button("Save Race Data"):
    try:
        df = pd.read_csv(pd.io.common.StringIO(horse_csv))

        st.success(f"Saved horse data for {track_name} Race {race_number} at {race_time}")

        st.write("Horse data preview:")
        st.dataframe(df, use_container_width=True)

        st.session_state["current_race_data"] = df
        st.session_state["current_track"] = track_name
        st.session_state["current_race_number"] = race_number
        st.session_state["current_race_time"] = race_time

    except Exception as error:
        st.error("Could not read horse CSV.")
        st.write(error)

st.subheader("4. Next Step")

st.info(
    "This version creates the meeting/race structure. "
    "Next we connect this screen back into the Golden Bullet scoring engine."
)