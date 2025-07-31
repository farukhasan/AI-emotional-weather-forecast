import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime
import json
import random
import google.generativeai as genai

# ------------------------------
# Streamlit page config
# ------------------------------
st.set_page_config(page_title="MoodCast AI 🌤️", page_icon="🌤️", layout="centered")

# ------------------------------
# Custom minimal Apple-like CSS
# ------------------------------
st.markdown("""
<style>
    html, body, [class*="css"] {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        background-color: #F9FAFB;
        color: #1F2937;
    }
    h1, h2, h3 {
        font-weight: 500;
        color: #111827;
    }
    .center-text {
        text-align: center;
        padding: 10px 0;
    }
    .card {
        background-color: white;
        border-radius: 16px;
        padding: 30px;
        margin: 30px 0;
        box-shadow: 0 10px 30px rgba(0,0,0,0.05);
    }
    .timestamp {
        font-size: 0.85em;
        color: #9CA3AF;
        margin-top: 1em;
        text-align: center;
    }
    .suggestion-title {
        font-weight: 600;
        margin-top: 15px;
        color: #2563EB;
    }
    .dos {
        color: #16A34A;
        margin-left: 20px;
    }
    .donts {
        color: #DC2626;
        margin-left: 20px;
    }
    .bold-move {
        color: #D97706;
        margin-left: 20px;
        font-weight: 700;
    }
</style>
""", unsafe_allow_html=True)

# ------------------------------
# Initialize Gemini AI
# ------------------------------
try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-pro')
except Exception as e:
    st.error("⚠️ Please set your GEMINI_API_KEY in Streamlit secrets to enable AI features.")
    st.stop()

# ------------------------------
# App Title & Header
# ------------------------------
st.markdown("""
<div class="center-text">
    <h1 style="font-size:3em;">🌤 MoodCast AI</h1>
    <p style="font-size:1.15em; color:#6B7280;">Your AI-Powered Emotional Weather Companion</p>
</div>
""", unsafe_allow_html=True)

# ------------------------------
# User inputs for mood and context
# ------------------------------
st.subheader("💬 How are you feeling today?")

cols = st.columns(3)
happiness = cols[0].slider("Happiness 😊", 0, 10, 5, help="Your current joy/contentment level")
stress = cols[1].slider("Stress 😟", 0, 10, 5, help="How tense or overwhelmed you feel")
energy = cols[2].slider("Energy ⚡", 0, 10, 5, help="Your alertness and vitality")

# Additional context for AI personalization
st.subheader("📝 Additional context (optional but helpful)")
profession = st.text_input("Your Profession (e.g., Teacher, Developer, Student)")
relationship = st.selectbox("Relationship Status", ["Single", "In a relationship", "Married", "It's complicated", "Prefer not to say"])
sleep_hours = st.slider("Hours of Sleep Last Night", 0.0, 12.0, 7.0, step=0.5)
stressors = st.text_area("Current Challenges or Stressors", placeholder="E.g., Work deadlines, family issues...")
events = st.text_area("Today's Important Events or Plans", placeholder="E.g., Presentation at 2pm, meeting with friend...")

# ------------------------------
# Session state to keep mood history and notes
# ------------------------------
if "mood_history" not in st.session_state:
    st.session_state.mood_history = []

if "mood_notes" not in st.session_state:
    st.session_state.mood_notes = []

# ------------------------------
# Helper: Save mood entry
# ------------------------------
def save_mood_entry():
    entry = {
        "timestamp": datetime.now().isoformat(),
        "date": datetime.now().strftime("%Y-%m-%d"),
        "happiness": happiness,
        "stress": stress,
        "energy": energy,
        "profession": profession,
        "relationship": relationship,
        "sleep_hours": sleep_hours,
        "stressors": stressors,
        "events": events,
    }
    st.session_state.mood_history.insert(0, entry)
    if len(st.session_state.mood_history) > 30:
        st.session_state.mood_history.pop()

# ------------------------------
# AI Prompt Template
# ------------------------------
def generate_ai_prompt(entry):
    prompt = f"""
You are an expert emotional wellness AI coach. Analyze the following person's current emotional state and environment, and generate a detailed emotional forecast.

CURRENT STATE:
- Happiness level: {entry['happiness']} / 10
- Stress level: {entry['stress']} / 10
- Energy level: {entry['energy']} / 10
- Hours of sleep last night: {entry['sleep_hours']}
- Profession: {entry['profession'] or 'Not specified'}
- Relationship status: {entry['relationship']}
- Current stressors: {entry['stressors'] or 'None specified'}
- Today's events: {entry['events'] or 'None specified'}

Your output should be a JSON with keys:
- forecast_summary: a creative and uplifting description of today's emotional weather
- confidence: percentage confidence of your analysis (e.g., '88%')
- dos: a list of 3 actionable things the user SHOULD do today
- donts: a list of 3 things the user should AVOID today
- bold_moves: 1 or 2 bold suggestions to improve their day
- emotional_tips: additional creative advice personalized for the user
- risk_factors: potential emotional pitfalls to watch out for
- power_moves: things to do to maximize emotional strength today

Respond ONLY with valid JSON.
"""
    return prompt

# ------------------------------
# AI Call function
# ------------------------------
def call_ai_model(prompt):
    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        # Remove markdown JSON code block if present
        if text.startswith("```json"):
            text = text[7:-3].strip()
        elif text.startswith("```"):
            text = text[3:-3].strip()
        return json.loads(text)
    except Exception as e:
        st.warning("⚠️ AI analysis failed, falling back to simple forecast.")
        return None

# ------------------------------
# Generate forecast on button click
# ------------------------------
if st.button("🔮 Generate My Emotional Forecast"):
    entry = {
        "happiness": happiness,
        "stress": stress,
        "energy": energy,
        "sleep_hours": sleep_hours,
        "profession": profession,
        "relationship": relationship,
        "stressors": stressors,
        "events": events,
    }
    save_mood_entry()
    prompt = generate_ai_prompt(entry)

    with st.spinner("🧠 Analyzing your emotional weather with AI..."):
        forecast = call_ai_model(prompt)

    # Fallback simple forecast if AI fails
    if forecast is None:
        mood_score = (happiness - stress + energy) / 3
        if mood_score >= 7:
            forecast = {
                "forecast_summary": "Bright and sunny emotional skies today! Your positivity shines.",
                "confidence": "90%",
                "dos": ["Spend time outside or with loved ones", "Celebrate your small wins", "Practice gratitude"],
                "donts": ["Avoid overthinking minor problems", "Don't isolate yourself", "Skip toxic conversations"],
                "bold_moves": ["Initiate a difficult but necessary conversation", "Try a new hobby today"],
                "emotional_tips": "Use your high energy to start a creative project.",
                "risk_factors": ["Beware of burnout if you overextend yourself."],
                "power_moves": ["Take short mindful breaks to recharge."]
            }
        elif mood_score >= 4:
            forecast = {
                "forecast_summary": "Partly cloudy with moments of calm. Take care of yourself.",
                "confidence": "75%",
                "dos": ["Take regular breaks", "Stay hydrated", "Connect with a friend"],
                "donts": ["Avoid multitasking", "Don't skip meals", "Avoid negative news"],
                "bold_moves": ["Say no to one non-essential task", "Meditate for 10 minutes"],
                "emotional_tips": "Focus on small achievable goals to boost mood.",
                "risk_factors": ["Possible mood dips late afternoon."],
                "power_moves": ["Gentle exercise can lift your spirits."]
            }
        else:
            forecast = {
                "forecast_summary": "Emotional rain showers with thunder. It's okay to rest.",
                "confidence": "70%",
                "dos": ["Practice deep breathing", "Reach out for support", "Journal your feelings"],
                "donts": ["Avoid stressful confrontations", "Don't isolate yourself", "Limit caffeine intake"],
                "bold_moves": ["Take a social media detox for the day", "Try a calming yoga session"],
                "emotional_tips": "Allow yourself to feel without judgment.",
                "risk_factors": ["Emotional vulnerability to triggers."],
                "power_moves": ["Self-compassion exercises will help."]
            }

    # Display Forecast beautifully
    st.markdown(f"""
    <div class="card">
        <h2 class="center-text">🌤 Emotional Forecast</h2>
        <p class="center-text" style="font-size:1.2em; font-weight:600;">{forecast['forecast_summary']}</p>
        <p class="center-text" style="color:#6B7280;">Confidence: {forecast.get('confidence', 'N/A')}</p>
        
        <div>
            <h3 class="suggestion-title">✅ What To Do</h3>
            <ul>
                {''.join([f'<li class="dos">{item}</li>' for item in forecast.get('dos', [])])}
            </ul>
        </div>
        
        <div>
            <h3 class="suggestion-title">❌ What To Avoid</h3>
            <ul>
                {''.join([f'<li class="donts">{item}</li>' for item in forecast.get('donts', [])])}
            </ul>
        </div>
        
        <div>
            <h3 class="suggestion-title">⚡ Bold Moves</h3>
            <ul>
                {''.join([f'<li class="bold-move">{item}</li>' for item in forecast.get('bold_moves', [])])}
            </ul>
        </div>
        
        <div>
            <h3 class="suggestion-title">💡 Emotional Tips</h3>
            <p>{forecast.get('emotional_tips', '')}</p>
        </div>
        
        <div>
            <h3 class="suggestion-title">⚠️ Risk Factors</h3>
            <ul>
                {''.join([f'<li>{item}</li>' for item in forecast.get('risk_factors', [])])}
            </ul>
        </div>
        
        <div>
            <h3 class="suggestion-title">🚀 Power Moves</h3>
            <ul>
                {''.join([f'<li>{item}</li>' for item in forecast.get('power_moves', [])])}
            </ul>
        </div>
        
        <p class="timestamp">Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
    </div>
    """, unsafe_allow_html=True)

# ------------------------------
# Mood Reflection & Journaling
# ------------------------------
st.subheader("📝 Reflect on your day (optional)")
note = st.text_area("Write anything about your mood, thoughts, or feelings...", height=120)

if st.button("💾 Save Reflection"):
    if note.strip():
        st.session_state.mood_notes.insert(0, {"date": datetime.now().strftime("%Y-%m-%d %H:%M"), "note": note})
        if len(st.session_state.mood_notes) > 30:
            st.session_state.mood_notes.pop()
        st.success("Your reflection was saved 🌱")
    else:
        st.warning("Please write something to save your reflection.")

# ------------------------------
# Mood History Visualization
# ------------------------------
if st.session_state.mood_history:
    st.subheader("📊 Mood Trends Over Time")
    df = pd.DataFrame(st.session_state.mood_history)
    df['datetime'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values('datetime')
    df['mood_score'] = (df['happiness'] - df['stress'] + df['energy']) / 3

    chart = alt.Chart(df).mark_line(point=True).encode(
        x=alt.X('datetime:T', title='Date & Time'),
        y=alt.Y('mood_score:Q', title='Mood Score (0-10)', scale=alt.Scale(domain=[0, 10])),
        tooltip=[
            alt.Tooltip('datetime:T', title='Timestamp'),
            alt.Tooltip('happiness:Q'),
            alt.Tooltip('stress:Q'),
            alt.Tooltip('energy:Q'),
            alt.Tooltip('mood_score:Q', format='.2f')
        ]
    ).properties(width=700, height=300)

    st.altair_chart(chart, use_container_width=True)

# ------------------------------
# Display Recent Reflections
# ------------------------------
if st.session_state.mood_notes:
    st.subheader("🗒️ Recent Reflections")
    for note in st.session_state.mood_notes[:5]:
        st.markdown(f"*{note['date']}*: {note['note']}")

# ------------------------------
# Footer with disclaimer
# ------------------------------
st.markdown("""
<div style="text-align:center; color:#9CA3AF; margin-top:40px; font-size:0.9em;">
    <em>⚠️ MoodCast AI is a wellness tool for self-awareness and not a replacement for professional mental health support.</em>
</div>
""", unsafe_allow_html=True)
