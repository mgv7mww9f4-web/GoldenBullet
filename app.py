import streamlit as st

st.set_page_config(
    page_title="Golden Bullet",
    page_icon="🏇",
    layout="wide"
)

st.title("🏇 Golden Bullet")

try:
    with open("golden_bullet_report.txt", "r") as f:
        report = f.read()

    st.text(report)

except:
    st.error("No report found. Run generate_report.py first.")