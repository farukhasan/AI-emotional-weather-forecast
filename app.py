import streamlit as st
import google.generativeai as genai
import pandas as pd
import plotly.graph_objects as go
import requests
from datetime import datetime, timedelta
import json
import time
import random
st.subheader("📧 Draft Leave Email to Manager")
st.code(st.session_state.leave_email, language="text")

copy_email_js = f"""
    <script>
    function copyToClipboard(text) {{
        navigator.clipboard.writeText(text).then(function() {{
            alert("Copied to clipboard!");
        }}, function(err) {{
            alert("Failed to copy text: " + err);
        }});
    }}
    </script>
    <button onclick="copyToClipboard(`{st.session_state.leave_email}`)">Copy Email</button>
"""
st.markdown(copy_email_js, unsafe_allow_html=True)

# Simple CSS with dark text on white background
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Lexend+Deca:wght@300;400;500;600;700&display=swap');
    
    .stApp {
        background-color: white;
        font-family: 'Lexend Deca', sans-serif;
    }
    /* Keep rest of your styles exactly the same */
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'assessments' not in st.session_state:
    st.session_state.assessments = []
if 'leave_email' not in st.session_state:
    st.session_state.leave_email = ""

# API Configuration
try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
    WEATHER_API_KEY = st.secrets.get("PIRATE_WEATHER_API_KEY", "")
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
except:
    st.error("🔑 Please add GEMINI_API_KEY to Streamlit secrets")
    st.stop()

def get_weather_tomorrow():
    try:
        if WEATHER_API_KEY:
            url = f"https://api.pirateweather.net/forecast/{WEATHER_API_KEY}/23.8103,90.4125"
            response = requests.get(url, timeout=3)
            data = response.json()
            tomorrow = data["daily"]["data"][1] if "daily" in data else data["currently"]
            return {
                "temp_high": round((tomorrow.get("temperatureHigh", 85) - 32) * 5/9),
                "temp_low": round((tomorrow.get("temperatureLow", 75) - 32) * 5/9),
                "condition": tomorrow.get("summary", "Partly cloudy"),
                "rain_chance": round(tomorrow.get("precipProbability", 0) * 100)
            }
    except:
        pass
    return {
        "temp_high": 30,
        "temp_low": 24,
        "condition": "Partly cloudy",
        "rain_chance": 20
    }

def analyze_leave_decision(data, weather):
    prompt = f"""You are an intelligent work-life balance advisor..."""  # (same as before)
    try:
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        if response_text.startswith('```json'):
            response_text = response_text.replace('```json', '').replace('```', '').strip()
        result = json.loads(response_text)
        required_fields = ['wellness_score', 'leave_type', 'confidence', 'main_reason', 'decision_summary']
        for field in required_fields:
            if field not in result:
                raise ValueError(f"Missing required field: {field}")
        return result
    except Exception as e:
        st.warning(f"AI analysis failed, using fallback logic: {str(e)}")
        stress_factor = (data['work_pressure'] + data['personal_stress']) / 2
        energy_factor = data['energy']
        sleep_factor = data['sleep']
        wellness = 100 - (stress_factor * 10) - ((10 - energy_factor) * 8) - ((10 - sleep_factor) * 6)
        wellness = max(5, min(100, int(wellness)))
        if wellness < 25:
            leave_type = "full_day_leave"
            decision = "Critical fatigue detected, full rest recommended."
        elif wellness < 45:
            leave_type = "half_day_leave"
            decision = "Moderate strain, partial rest could help."
        elif wellness < 65:
            leave_type = "work_with_care"
            decision = "Work with caution and self-care."
        else:
            leave_type = "work_normally"
            decision = "Fit to work."
        return {
            "wellness_score": wellness,
            "leave_type": leave_type,
            "confidence": 75,
            "main_reason": "Fallback assessment",
            "decision_summary": decision,
            "work_activities": ["Take regular breaks", "Prioritize essential tasks", "Stay hydrated"],
            "work_avoid": ["Overtime", "Extra commitments", "Skipping meals"],
            "leave_activities": ["Rest", "Light activity", "Hobby time", "Social connection"],
            "leave_avoid": ["Work emails", "Intense exercise", "Stressful decisions"],
            "warning_signs": ["Inability to focus", "Physical illness", "Anxiety spikes"],
            "recovery_estimate": "1-3 days"
        }

def generate_random_leave_email():
    excuses = [
        "I’m feeling quite unwell since last night with severe stomach cramps and will not be able to attend work tomorrow.",
        "I have a sudden bout of food poisoning and need to rest and recover at home tomorrow.",
        "A close family member has been taken ill and I need to be with them, so I won’t be in tomorrow.",
        "I’m experiencing high fever and weakness, and will take a sick day tomorrow to recover.",
        "I need to manage an urgent personal matter that has come up unexpectedly, so I’ll be away tomorrow."
    ]
    chosen_excuse = random.choice(excuses)
    email_text = f"Hi [Manager's Name],\n\n{chosen_excuse}\n\nRegards,\n[Your Name]"
    return email_text

def main():
    st.markdown('<h1 style="text-align: center;">Should I Take Leave Tomorrow?</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center;">AI-powered decision making for your work-life balance</p>', unsafe_allow_html=True)

    weather = get_weather_tomorrow()

    # Weather card (same code as before)...

    st.markdown('<h3>How are you feeling today?</h3>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)

    with col1:
        mood = st.selectbox("Overall mood", ["Excellent", "Good", "Okay", "Struggling", "Overwhelmed", "Exhausted"])
        energy = st.slider("Energy level", 1, 10, 5)
        sleep = st.slider("Last night's sleep quality", 1, 10, 6)

    with col2:
        work_pressure = st.slider("Work pressure level", 1, 10, 5)
        personal_stress = st.slider("Personal life stress", 1, 10, 4)
        physical_symptoms = st.selectbox("Physical symptoms", ["None", "Mild tension/headache", "Moderate discomfort", "Severe symptoms"])

    last_break = st.selectbox("When did you last take a day off?", ["Never", "6+ months ago", "2-6 months ago", "1-2 months ago", "Within last month"])
    tomorrow_importance = st.selectbox("How critical is tomorrow's work?", ["Low priority - routine tasks", "Medium - some important items", "High - major deadlines", "Critical - cannot be postponed"])
    support = st.selectbox("Your support system", ["Strong", "Good", "Limited", "Weak"])

    # NEW: leave balance input
    leave_min, leave_max = st.slider("Estimated leaves left this year", 0, 30, (5, 10))
    if leave_max <= 3:
        st.info("⚠️ You have very few leaves left. Consider saving them unless absolutely necessary.")
    elif leave_max <= 8:
        st.info("📅 You have some leaves left, but use them wisely if you have future plans.")
    else:
        st.info("✅ You have plenty of leaves left. Taking one tomorrow is fine if needed.")

    if st.button("Get My Personalized Recommendation", type="primary"):
        data = {
            'mood': mood,
            'energy': energy,
            'sleep': sleep,
            'work_pressure': work_pressure,
            'personal_stress': personal_stress,
            'physical_symptoms': physical_symptoms,
            'last_break': last_break,
            'tomorrow_importance': tomorrow_importance,
            'support': support
        }
        analysis = analyze_leave_decision(data, weather)

        st.session_state.leave_email = generate_random_leave_email()

        # Decision card (same styling as before)...

        # NEW: Leave email section
        st.subheader("📧 Draft Leave Email to Manager")
        st.code(st.session_state.leave_email, language="text")
        if st.button("Copy Email"):
            pyperclip.copy(st.session_state.leave_email)
            st.success("Copied to clipboard!")

if __name__ == "__main__":
    main()

