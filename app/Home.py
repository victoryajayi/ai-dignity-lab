import streamlit as st

st.set_page_config(page_title="AI Dignity Lab", page_icon="🔍")

st.title("AI Dignity Lab")
st.write("Paste AI-written text below to check it for fairness, respect, and access.")

text = st.text_area("Text to check", height=200)

if st.button("Check text"):
    if text.strip():
        st.success(f"Received {len(text.split())} words. Checks coming soon.")
    else:
        st.warning("Please paste some text first.")
