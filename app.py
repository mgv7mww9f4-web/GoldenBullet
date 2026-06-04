from datetime import date

import requests
import streamlit as st

st.set_page_config(
    page_title="FormFav Test",
    page_icon="🏇",
    layout="wide"
)

st.title("🏇 FormFav Raw Data Test")

try:
    FORMFAV_API_KEY = st.secrets["FORMFAV_API_KEY"]
    st.success(f"FormFav API Connected: {FORMFAV_API_KEY[:6]}...")
except Exception:
    FORMFAV_API_KEY = None
    st.error("FormFav API key not found. Add FORMFAV_API_KEY to Streamlit Secrets.")

st.write("This test shows the raw data from FormFav so we can map it properly into Golden Bullet.")

race_date = st.date_input("Race date", value=date.today())
track = st.text_input("Track", value="Sandown")
race = st.number_input("Race number", min_value=1, max_value=20, value=1)

if st.button("Load Raw FormFav Data"):
    if FORMFAV_API_KEY is None:
        st.error("No FormFav API key found.")
    else:
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

        try:
            response = requests.get(
                url,
                headers=headers,
                params=params,
                timeout=30
            )

            st.write("Status code:", response.status_code)
            st.write("URL:", response.url)

            try:
                data = response.json()

                st.subheader("Raw FormFav Data")
                st.json(data)

                st.subheader("Copy This")
                st.write("Open the first horse in the JSON above, then copy and paste it to ChatGPT.")

            except Exception:
                st.subheader("Raw Text Response")
                st.text(response.text)

        except Exception as error:
            st.error("Could not load FormFav data.")
            st.write(error)