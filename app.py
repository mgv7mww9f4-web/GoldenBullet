from io import StringIO

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
    API_KEY = st.secrets["ODDS_API_KEY"]
    st.success(f"Odds API Connected: {API_KEY[:6]}...")
except Exception:
    API_KEY = None
    st.error("Odds API key not found. Add ODDS_API_KEY to Streamlit Secrets.")


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

    if value in ["", "x", "-", "nan"]:
        return 0

    try:
        return int(float(value))
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


def fetch_sports():
    url = "https://api.the-odds-api.com/v4/sports"
    response = requests.get(
        url,
        params={
            "apiKey": API_KEY,
            "all": "true"
        },
        timeout=20
    )

    if response.status_code != 200:
        raise Exception(response.text)

    return response.json()


def fetch_odds(sport_key, market):
    url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds"

    response = requests.get(
        url,
        params={
            "apiKey": API_KEY,
            "regions": "au",
            "markets": market,
            "oddsFormat": "decimal",
            "dateFormat": "iso"
        },
        timeout=20
    )

    if response.status_code != 200:
        raise Exception(response.text)

    return response.json(), response.headers


def find_racing_sports(sports):
    racing_sports = []

    for sport in sports:
        combined_text = (
            str(sport.get("key", "")) + " " +
            str(sport.get("group", "")) + " " +
            str(sport.get("title", "")) + " " +
            str(sport.get("description", ""))
        ).lower()

        if "horse" in combined_text or "racing" in combined_text:
            racing_sports.append(sport)

    return racing_sports


def odds_events_to_table(events):
    rows = []

    for event in events:
        event_name = event.get("home_team") or event.get("title") or event.get("id")

        for bookmaker in event.get("bookmakers", []):
            bookmaker_name = bookmaker.get("title", bookmaker.get("key", "Unknown"))

            for market in bookmaker.get("markets", []):
                market_key = market.get("key", "")

                for outcome in market.get("outcomes", []):
                    rows.append({
                        "event_id": event.get("id"),
                        "event": event_name,
                        "commence_time": event.get("commence_time"),
                        "bookmaker": bookmaker_name,
                        "market": market_key,
                        "runner": outcome.get("name"),
                        "odds": outcome.get("price")
                    })

    return pd.DataFrame(rows)


def odds_table_to_csv(df, race_number):
    csv_rows = []

    for index, row in df.iterrows():
        csv_rows.append({
            "horse_number": index + 1,
            "horse_name": row["runner"],
            "race_number": race_number,
            "grade": "API",
            "barrier": 0,
            "jockey": "Unknown",
            "trainer": "Unknown",
            "odds": row["odds"],
            "last_start_position": 0,
            "second_last_position": 0,
            "third_last_position": 0,
            "distance_range": "Unknown",
            "weight_carried": 0,
            "track_condition": "Unknown",
            "weather": "Unknown",
            "sky_rating": 0
        })

    return pd.DataFrame(csv_rows).to_csv(index=False)


def display_scored_race(scored_df, bankroll):
    st.success("Race scored successfully!")

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


st.write(
    "Use the Odds API test section first. If horse racing appears, load odds, "
    "turn them into CSV, then add missing form/barrier/weight data if needed."
)

bankroll = st.number_input("Bankroll", min_value=1.0, value=150.0, step=1.0)

tab1, tab2 = st.tabs(["Live Odds API", "Manual CSV Scorer"])

with tab1:
    st.subheader("1. Find Racing Sports From The Odds API")

    if API_KEY is None:
        st.error("Add ODDS_API_KEY in Streamlit Secrets first.")
    else:
        if st.button("Load Available Sports"):
            try:
                sports = fetch_sports()
                racing_sports = find_racing_sports(sports)

                st.session_state["sports"] = sports
                st.session_state["racing_sports"] = racing_sports

                st.success(f"Loaded {len(sports)} sports.")
                st.write(f"Found {len(racing_sports)} racing-related sports.")

            except Exception as error:
                st.error("Could not load sports.")
                st.write(error)

    if "racing_sports" in st.session_state:
        racing_sports = st.session_state["racing_sports"]

        if len(racing_sports) == 0:
            st.warning("No horse racing sports found on your current Odds API plan/feed.")
            st.write("All available sports:")
            st.dataframe(pd.DataFrame(st.session_state["sports"]), use_container_width=True)
        else:
            sport_options = {
                f"{sport.get('title')} | {sport.get('key')}": sport.get("key")
                for sport in racing_sports
            }

            selected_sport_label = st.selectbox(
                "Select racing sport",
                list(sport_options.keys())
            )

            selected_sport_key = sport_options[selected_sport_label]

            market = st.selectbox(
                "Market",
                ["h2h", "outrights"],
                index=0
            )

            if st.button("Load Odds For Selected Sport"):
                try:
                    events, headers = fetch_odds(selected_sport_key, market)

                    st.session_state["odds_events"] = events
                    st.session_state["odds_headers"] = dict(headers)

                    st.success(f"Loaded {len(events)} events.")
                    st.write(
                        "Requests remaining:",
                        headers.get("x-requests-remaining", "Unknown")
                    )

                except Exception as error:
                    st.error("Could not load odds.")
                    st.write(error)

    if "odds_events" in st.session_state:
        st.subheader("2. Odds Results")

        events = st.session_state["odds_events"]

        if len(events) == 0:
            st.warning("No odds returned for this sport/market.")
        else:
            odds_df = odds_events_to_table(events)

            if len(odds_df) == 0:
                st.warning("Events loaded, but no bookmaker outcomes were found.")
                st.json(events[0])
            else:
                st.dataframe(odds_df, use_container_width=True)

                events_list = sorted(odds_df["event"].dropna().unique())

                selected_event = st.selectbox(
                    "Select event/race",
                    events_list
                )

                event_df = odds_df[odds_df["event"] == selected_event]

                bookmakers = sorted(event_df["bookmaker"].dropna().unique())

                selected_bookmaker = st.selectbox(
                    "Select bookmaker",
                    bookmakers
                )

                bookmaker_df = event_df[event_df["bookmaker"] == selected_bookmaker]

                race_number = st.number_input(
                    "Race number for CSV",
                    min_value=1,
                    max_value=20,
                    value=1,
                    key="api_race_number"
                )

                generated_csv = odds_table_to_csv(bookmaker_df, race_number)

                st.subheader("3. Generated CSV From Odds API")
                st.write("This includes names and odds. Add form/barrier/weight/Sky Rating later if you have them.")

                api_csv = st.text_area(
                    "Generated CSV",
                    value=generated_csv,
                    height=300
                )

                if st.button("Score API CSV"):
                    try:
                        df = pd.read_csv(StringIO(api_csv))
                        scored_df = calculate_scores(df)
                        display_scored_race(scored_df, bankroll)
                    except Exception as error:
                        st.error("Could not score API CSV.")
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