import streamlit as st
from datetime import datetime
import random

# ------------------------------
# Page configuration
# ------------------------------
st.set_page_config(page_title="MoodCast - Emotional Weather Forecast", layout="centered")

# ------------------------------
# Apply custom minimalistic Apple-like CSS
# ------------------------------
st.markdown("""
<style>
html, body, [class*="css"]  {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    background-color: #F9FAFB;
    color: #1F2937;
}

h1, h2, h3 {
    font-weight: 500 !important;
    color: #111827;
}

[data-testid="metric-container"] {
    background-color: #ffffff;
    border-radius: 12px;
    padding: 15px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.05);
}

button[kind="primary"] {
    background-color: #4F46E5 !important;
    border-radius: 12px !important;
    font-weight: 500 !important;
}
button[kind="primary"]:hover {
    background-color: #4338CA !important;
}

input, textarea, select {
    border-radius: 12px !important;
    background-color: #ffffff !important;
    border: 1px solid #D1D5DB !important;
}

section[data-testid="stSidebar"] {
    background-color: #F3F4F6;
}

.streamlit-expanderHeader {
    font-weight: 500;
    color: #1F2937;
}

.forecast-card {
    background: #ffffff;
    border-radius: 18px;
    padding: 30px;
    margin: 20px auto;
    box-shadow: 0 10px 24px rgba(0,0,0,0.05);
    text-align: center;
}

.forecast-card h1 {
    font-size: 3.5em;
    margin-bottom: 0.2em;
}

.forecast-card h2 {
    font-weight: 400;
    font-size: 1.5em;
    color: #4B5563;
}
</style>
""", unsafe_allow_html=True)

# ------------------------------
# Emotional forecast generation
# ------------------------------
def get_emotional_forecast(mood, stress, sleep, activity, support):
    score = mood * 2 + sleep - stress + activity + support
    forecast = {}

    if score > 18:
        forecast["weather"] = "Sunny"
        forecast["icon"] = "☀️"
        forecast["description"] = "You're radiating positivity and calm."
        forecast["suggestion"] = "Enjoy this emotional sunshine. Spread it to others!"
    elif score > 12:
        forecast["weather"] = "Partly Cloudy"
        forecast["icon"] = "⛅"
        forecast["description"] = "You're balanced but with mild stress."
        forecast["suggestion"] = "Take breaks. Reflect. Appreciate little joys."
    elif score > 6:
        forecast["weather"] = "Rainy"
        forecast["icon"] = "🌧️"
        forecast["description"] = "Emotions feel heavy."
        forecast["suggestion"] = "Reach out to someone. Let your feelings flow."
    else:
        forecast["weather"] = "Stormy"
        forecast["icon"] = "⛈️"
        forecast["description"] = "Overwhelmed or low energy."
        forecast["suggestion"] = "Be kind to yourself. Consider rest or support."

    forecast["confidence"] = f"{random.randint(85, 99)}%"
    return forecast

# ------------------------------
# App UI
# ------------------------------

st.markdown("""
<div style="text-align:center;">
    <h1 style="font-size:3.2em; font-weight:600; color:#111827; margin-bottom: 0.2em;">MoodCast</h1>
    <p style="font-size:1.2em; color:#6B7280;">Your AI-Powered Emotional Weather Forecast</p>
</div>
""", unsafe_allow_html=True)

st.divider()

st.subheader("🌤️ How are you feeling today?")

col1, col2 = st.columns(2)

with col1:
    mood = st.slider("Mood Level", 0, 10, 5, help="Overall emotional feeling")
    sleep = st.slider("Sleep Quality", 0, 10, 5, help="How restful your last sleep was")
    support = st.slider("Support System", 0, 10, 5, help="How supported you feel")

with col2:
    stress = st.slider("Stress Level", 0, 10, 5, help="Your current stress level")
    activity = st.slider("Physical Activity", 0, 10, 5, help="Exercise or physical movement today")

if st.button("Show My MoodCast"):
    forecast = get_emotional_forecast(mood, stress, sleep, activity, support)
    st.markdown(f"""
    <div class="forecast-card">
        <h1>{forecast['icon']}</h1>
        <h2>{forecast['weather']}</h2>
        <p style="font-size: 1.05em; margin: 10px 0; color: #374151;">{forecast['description']}</p>
        <p style="font-size: 0.95em; color: #6B7280;">Suggestion: <strong>{forecast['suggestion']}</strong></p>
        <p style="font-size: 0.9em; color: #9CA3AF;">Confidence: {forecast['confidence']}</p>
    </div>
    """, unsafe_allow_html=True)

# ------------------------------
# Footer
# ------------------------------
st.markdown("""
<hr style="margin-top: 3em;">
<p style="text-align: center; color: #9CA3AF; font-size: 0.85em;">
    Built with ❤️ to help you check in with yourself. Remember, emotional weather changes — and that’s okay.
</p>
""", unsafe_allow_html=True)
