import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv
import os

# === CONFIG ===
load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-pro")

st.set_page_config(page_title="Should I Take Leave Tomorrow?", layout="centered")
st.markdown("""
    <style>
        html, body, [class*="css"]  {
            font-family: 'Lexend Deca', sans-serif;
            background-color: #f6f8fa;
            color: #1a1a1a;
        }
        .result-card {
            animation: fadeIn 0.8s ease-in-out;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
    </style>
""", unsafe_allow_html=True)

# === TITLE ===
st.title("🧠 Should I Take Leave Tomorrow?")
st.caption("An AI-powered emotional weather advisor")

st.markdown("""<hr style="border: 1px solid #e0e0e0;">""", unsafe_allow_html=True)

# === INPUTS ===
st.header("📋 How are you today?")

mood = st.selectbox("How would you describe your mood?", ["Happy", "Anxious", "Stressed", "Tired", "Neutral", "Sad"])
stress_level = st.slider("Stress Level", 0, 10, 5)
weather = st.selectbox("Today's Weather", ["Sunny", "Cloudy", "Rainy", "Stormy", "Cold", "Hot"])
workload = st.selectbox("Workload Intensity", ["Light", "Moderate", "Heavy"])
sleep_hours = st.slider("How many hours did you sleep last night?", 0, 12, 6)

st.markdown("""<hr style="border: 1px solid #e0e0e0;">""", unsafe_allow_html=True)

# === PROCESSING ===
if st.button("🔍 Analyze & Decide"):
    with st.spinner("Thinking... ✨"):
        prompt = f"""
        You are an emotional wellness advisor. Given the inputs:
        - Mood: {mood}
        - Stress Level: {stress_level}/10
        - Weather: {weather}
        - Workload: {workload}
        - Sleep: {sleep_hours} hours

        Analyze and answer:
        1. Should the person take leave tomorrow? (Yes/No)
        2. Why?
        3. What should they do instead if not taking leave?
        4. Suggest 2 relaxing or energizing activities based on their mood and weather.
        5. Return a wellness score (0-100).
        """

        response = model.generate_content(prompt)
        analysis = response.text

        st.markdown("""
        <div class="result-card" style="background: #007aff; border-radius: 16px; padding: 2rem; color: white; text-align: center;
            margin: 2rem 0; box-shadow: 0 4px 20px rgba(0, 122, 255, 0.15);">
            <h2 style="margin: 0;">💡 Recommendation</h2>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"<div class='result-card' style='background: white; border-radius: 16px; padding: 1.5rem; color: #333; box-shadow: 0 4px 10px rgba(0,0,0,0.05); font-size: 16px;'>
        {analysis}
        </div>", unsafe_allow_html=True)

        # Extracting and showing a mock wellness score from the output (ideally parse more accurately)
        import re
        match = re.search(r'(\\d{1,3})\\s*[%]?', analysis)
        if match:
            score = int(match.group(1))
            if 0 <= score <= 100:
                st.progress(score, text=f"Wellness Score: {score}%")
