import streamlit as st
import google.generativeai as genai
import pandas as pd
import plotly.graph_objects as go
import requests
from datetime import datetime, timedelta
import json
import time

# Page config
st.set_page_config(
    page_title="Should I Take Leave Tomorrow?",
    page_icon="🌅",
    layout="centered"
)

# Beautiful modern CSS with dark theme and neon accents
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&display=swap');
    
    .stApp {
        background: linear-gradient(135deg, #0f0f23 0%, #1a1a2e 50%, #16213e 100%);
        font-family: 'Space Grotesk', sans-serif;
        color: #e2e8f0;
    }
    
    .main-title {
        font-size: 3rem;
        font-weight: 700;
        text-align: center;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 0.5rem;
        animation: titleGlow 3s ease-in-out infinite alternate;
    }
    
    @keyframes titleGlow {
        from { filter: drop-shadow(0 0 20px rgba(102, 126, 234, 0.3)); }
        to { filter: drop-shadow(0 0 30px rgba(102, 126, 234, 0.6)); }
    }
    
    .subtitle {
        font-size: 1.2rem;
        text-align: center;
        color: #94a3b8;
        margin-bottom: 3rem;
        font-weight: 400;
    }
    
    .neon-card {
        background: rgba(30, 41, 59, 0.9);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(148, 163, 184, 0.3);
        border-radius: 20px;
        padding: 2rem;
        margin: 1.5rem 0;
        box-shadow: 
            0 8px 32px rgba(0, 0, 0, 0.3),
            inset 0 1px 0 rgba(255, 255, 255, 0.1);
        position: relative;
        overflow: hidden;
    }
    
    .weather-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        text-align: center;
    }
    
    .decision-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        text-align: center;
        margin: 2rem 0;
        border: 2px solid;
        border-image: linear-gradient(45deg, #ff006e, #8338ec, #3a86ff) 1;
        box-shadow: 0 0 30px rgba(102, 126, 234, 0.5);
    }
    
    .wellness-meter {
        background: rgba(15, 23, 42, 0.8);
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1rem 0;
        border: 1px solid rgba(59, 130, 246, 0.3);
    }
    
    .wellness-bar {
        width: 100%;
        height: 20px;
        background: rgba(30, 41, 59, 0.8);
        border-radius: 10px;
        overflow: hidden;
        position: relative;
    }
    
    .wellness-fill {
        height: 100%;
        background: linear-gradient(90deg, #ef4444, #f59e0b, #10b981);
        border-radius: 10px;
        transition: width 2s ease-out;
        box-shadow: 0 0 20px rgba(16, 185, 129, 0.4);
    }
    
    .recommendation-pill {
        display: inline-block;
        padding: 0.75rem 1.5rem;
        margin: 0.5rem;
        border-radius: 25px;
        font-weight: 500;
        font-size: 0.9rem;
        border: 1px solid;
        backdrop-filter: blur(10px);
        transition: all 0.3s ease;
    }
    
    .pill-positive {
        background: rgba(16, 185, 129, 0.2);
        border-color: rgba(16, 185, 129, 0.4);
        color: #6ee7b7;
    }
    
    .pill-positive:hover {
        background: rgba(16, 185, 129, 0.3);
        box-shadow: 0 5px 15px rgba(16, 185, 129, 0.3);
        transform: translateY(-2px);
    }
    
    .pill-negative {
        background: rgba(239, 68, 68, 0.2);
        border-color: rgba(239, 68, 68, 0.4);
        color: #fca5a5;
    }
    
    .pill-negative:hover {
        background: rgba(239, 68, 68, 0.3);
        box-shadow: 0 5px 15px rgba(239, 68, 68, 0.3);
        transform: translateY(-2px);
    }
    
    .mood-emoji {
        font-size: 3rem;
        margin: 1rem 0;
        animation: bounce 2s infinite;
    }
    
    @keyframes bounce {
        0%, 20%, 50%, 80%, 100% { transform: translateY(0); }
        40% { transform: translateY(-10px); }
        60% { transform: translateY(-5px); }
    }
    
    .stButton > button {
        width: 100%;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 15px;
        padding: 1rem 2rem;
        font-weight: 600;
        font-size: 1.1rem;
        margin-top: 2rem;
        font-family: 'Space Grotesk', sans-serif;
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-3px);
        box-shadow: 0 12px 35px rgba(102, 126, 234, 0.6);
    }
    
    .stSelectbox > div > div,
    .stSlider > div > div {
        background: rgba(30, 41, 59, 0.8) !important;
        border: 1px solid rgba(59, 130, 246, 0.3) !important;
        border-radius: 10px !important;
        color: #e2e8f0 !important;
    }
    
    .stSelectbox label,
    .stSlider label,
    label[data-testid="stWidgetLabel"] {
        color: #e2e8f0 !important;
        font-family: 'Space Grotesk', sans-serif !important;
        font-weight: 500 !important;
        font-size: 1rem !important;
    }
    
    .ai-thinking {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        color: #8b5cf6;
        font-weight: 500;
        font-size: 1.2rem;
    }
    
    .thinking-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #8b5cf6;
        animation: thinkingPulse 1.4s infinite;
    }
    
    .thinking-dot:nth-child(2) { animation-delay: 0.2s; }
    .thinking-dot:nth-child(3) { animation-delay: 0.4s; }
    
    @keyframes thinkingPulse {
        0%, 60%, 100% { transform: scale(0.8); opacity: 0.5; }
        30% { transform: scale(1.2); opacity: 1; }
    }
    
    .info-card {
        background: rgba(15, 23, 42, 0.8);
        border: 1px solid rgba(148, 163, 184, 0.2);
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        color: #e2e8f0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'assessments' not in st.session_state:
    st.session_state.assessments = []

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
    """Get tomorrow's weather forecast"""
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

def get_mood_emoji(mood):
    """Get emoji based on mood"""
    mood_map = {
        "Excellent": "😊",
        "Good": "🙂", 
        "Okay": "😐",
        "Struggling": "😔",
        "Overwhelmed": "😰",
        "Exhausted": "😴"
    }
    return mood_map.get(mood, "🙂")

def create_wellness_meter(score):
    """Create an animated wellness meter"""
    return f"""
    <div class="wellness-meter">
        <h4 style="margin: 0 0 1rem 0; color: #e2e8f0; text-align: center;">Wellness Score: {score}/100</h4>
        <div class="wellness-bar">
            <div class="wellness-fill" style="width: {score}%;"></div>
        </div>
        <div style="text-align: center; margin-top: 0.5rem; font-size: 0.9rem; color: #94a3b8;">
            {'🔴 Critical' if score < 25 else '🟡 Needs Care' if score < 50 else '🟢 Good' if score < 75 else '✨ Excellent'}
        </div>
    </div>
    """

def analyze_leave_decision(data, weather):
    """Enhanced AI analysis for leave recommendation"""
    
    prompt = f"""You are an intelligent work-life balance advisor. Analyze if this person should take leave tomorrow based on their mental state, workload, and external factors.

CURRENT STATE:
- Overall feeling: {data['mood']}
- Energy level: {data['energy']}/10
- Stress level: {data['stress']}/10
- Sleep quality: {data['sleep']}/10
- Work pressure: {data['work_pressure']}/10
- Personal life stress: {data['personal_stress']}/10
- Physical symptoms: {data['physical_symptoms']}
- Last break taken: {data['last_break']}
- Tomorrow's work importance: {data['tomorrow_importance']}
- Support system: {data['support']}

WEATHER TOMORROW: {weather['temp_high']}°C/{weather['temp_low']}°C, {weather['condition']}, {weather['rain_chance']}% rain chance

Respond in this EXACT JSON format:
{{
    "wellness_score": 45,
    "leave_type": "full_day_leave",
    "confidence": 82,
    "main_reason": "Primary reason for recommendation",
    "decision_summary": "Brief 2-sentence explanation of the decision",
    "work_activities": ["Take regular breaks", "Prioritize essential tasks", "Stay hydrated"],
    "work_avoid": ["Overtime", "Perfectionism", "Skipping breaks"],
    "leave_activities": ["Sleep well", "Light exercise", "Do something enjoyable", "Connect with people"],
    "leave_avoid": ["Check work emails", "Intensive activities", "Major decisions"],
    "warning_signs": ["Panic attacks", "Complete inability to focus", "Persistent symptoms"],
    "recovery_estimate": "1-3 days with proper rest"
}}

Leave types: "full_day_leave", "half_day_leave", "work_with_care", "work_normally"
"""

    try:
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        if response_text.startswith('```json'):
            response_text = response_text.replace('```json', '').replace('```', '').strip()
        
        result = json.loads(response_text)
        return result
        
    except Exception as e:
        # Fallback logic
        stress_factor = (data['stress'] + data['work_pressure'] + data['personal_stress']) / 3
        energy_factor = data['energy']
        sleep_factor = data['sleep']
        
        wellness = 100 - (stress_factor * 10) - ((10 - energy_factor) * 8) - ((10 - sleep_factor) * 6)
        wellness = max(5, min(100, int(wellness)))
        
        if wellness < 25:
            leave_type = "full_day_leave"
            decision = "Your stress levels are critically high. A full day of rest is essential."
        elif wellness < 45:
            leave_type = "half_day_leave"
            decision = "Moderate stress levels suggest you need some recovery time."
        elif wellness < 65:
            leave_type = "work_with_care"
            decision = "You can work but need to be careful with your energy."
        else:
            leave_type = "work_normally"
            decision = "You're in good shape to work tomorrow."
        
        return {
            "wellness_score": wellness,
            "leave_type": leave_type,
            "confidence": 75,
            "main_reason": f"Stress {stress_factor:.1f}/10, Energy {energy_factor}/10",
            "decision_summary": decision,
            "work_activities": ["Take regular breaks", "Prioritize essential tasks", "Stay hydrated"],
            "work_avoid": ["Overtime", "Perfectionism", "Skipping breaks"],
            "leave_activities": ["Sleep well", "Light exercise", "Do something enjoyable", "Connect with people"],
            "leave_avoid": ["Check work emails", "Intensive activities", "Major decisions"],
            "warning_signs": ["Panic attacks", "Complete inability to focus", "Persistent symptoms"],
            "recovery_estimate": "1-3 days with proper rest"
        }

def main():
    # Animated header
    st.markdown('''
    <h1 class="main-title">Should I Take Leave Tomorrow?</h1>
    <p class="subtitle">✨ AI-powered decision making for your work-life balance</p>
    ''', unsafe_allow_html=True)
    
    # Get tomorrow's weather
    weather = get_weather_tomorrow()
    
    # Weather display
    weather_condition_lower = weather['condition'].lower()
    if 'rain' in weather_condition_lower:
        weather_icon = "🌧️"
    elif 'cloud' in weather_condition_lower:
        weather_icon = "☁️"
    elif 'sun' in weather_condition_lower or 'clear' in weather_condition_lower:
        weather_icon = "☀️"
    else:
        weather_icon = "🌤️"
    
    st.markdown(f'''
    <div class="neon-card weather-card">
        <h3 style="margin: 0 0 1rem 0; font-weight: 600;">Tomorrow's Weather</h3>
        <div style="font-size: 3rem; margin: 1rem 0;">{weather_icon}</div>
        <div style="font-size: 1.3rem; font-weight: 600; margin: 0.5rem 0;">
            {weather['temp_high']}°C / {weather['temp_low']}°C
        </div>
        <div style="opacity: 0.9; font-size: 1rem;">
            {weather['condition']} • {weather['rain_chance']}% chance of rain
        </div>
    </div>
    ''', unsafe_allow_html=True)
    
    # Input section
    st.markdown('<div class="neon-card">', unsafe_allow_html=True)
    st.markdown('<h3 style="color: #e2e8f0; font-weight: 600; margin-bottom: 1.5rem;">How are you feeling today?</h3>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        mood = st.selectbox(
            "Overall mood",
            ["Excellent", "Good", "Okay", "Struggling", "Overwhelmed", "Exhausted"],
            help="How would you describe your general state today?"
        )
        
        # Display mood emoji
        st.markdown(f'<div class="mood-emoji" style="text-align: center;">{get_mood_emoji(mood)}</div>', unsafe_allow_html=True)
        
        energy = st.slider("Energy level", 1, 10, 5)
        stress = st.slider("Current stress", 1, 10, 5)
        sleep = st.slider("Sleep quality", 1, 10, 6)
        
    with col2:
        work_pressure = st.slider("Work pressure", 1, 10, 5)
        personal_stress = st.slider("Personal stress", 1, 10, 4)
        
        physical_symptoms = st.selectbox(
            "Physical symptoms",
            ["None", "Mild tension/headache", "Moderate discomfort", "Severe symptoms"]
        )
        
        last_break = st.selectbox(
            "Last day off",
            ["Within last month", "1-2 months ago", "2-6 months ago", "6+ months ago", "Never"]
        )
    
    tomorrow_importance = st.selectbox(
        "Tomorrow's work priority",
        ["Low priority", "Medium priority", "High priority", "Critical priority"]
    )
    
    support = st.selectbox(
        "Support system",
        ["Strong support", "Good support", "Limited support", "Feeling isolated"]
    )
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Analysis button
    if st.button("🚀 Analyze My Situation with AI", type="primary"):
        data = {
            'mood': mood,
            'energy': energy,
            'stress': stress,
            'sleep': sleep,
            'work_pressure': work_pressure,
            'personal_stress': personal_stress,
            'physical_symptoms': physical_symptoms,
            'last_break': last_break,
            'tomorrow_importance': tomorrow_importance,
            'support': support
        }
        
        # AI thinking animation
        thinking_placeholder = st.empty()
        thinking_placeholder.markdown('''
        <div style="text-align: center; padding: 2rem;">
            <div class="ai-thinking">
                🤖 AI is analyzing your situation
                <div class="thinking-dot"></div>
                <div class="thinking-dot"></div>
                <div class="thinking-dot"></div>
            </div>
        </div>
        ''', unsafe_allow_html=True)
        
        time.sleep(2)
        thinking_placeholder.empty()
        
        analysis = analyze_leave_decision(data, weather)
        
        # Wellness meter
        st.markdown(create_wellness_meter(analysis['wellness_score']), unsafe_allow_html=True)
        
        # Decision display
        leave_type_map = {
            "full_day_leave": ("🏠 Take Full Day Off", "🔴"),
            "half_day_leave": ("⏰ Take Half Day", "🟡"),
            "work_with_care": ("⚠️ Work With Care", "🟠"),
            "work_normally": ("💼 Work Normally", "🟢")
        }
        
        decision_text, status_icon = leave_type_map.get(analysis['leave_type'], ("Work With Care", "🟡"))
        
        st.markdown(f'''
        <div class="neon-card decision-card">
            <h2 style="margin: 0; font-weight: 700; font-size: 1.8rem;">{decision_text}</h2>
            <div style="font-size: 2rem; margin: 1rem 0;">{status_icon}</div>
            <p style="font-size: 1.1rem; margin: 1rem 0; line-height: 1.6;">{analysis['decision_summary']}</p>
            <div style="font-size: 0.9rem; opacity: 0.8; margin-top: 1.5rem;">
                Confidence: {analysis['confidence']}% | {analysis['main_reason']}
            </div>
        </div>
        ''', unsafe_allow_html=True)
        
        # Recommendations
        col1, col2 = st.columns(2)
        
        if analysis['leave_type'] in ['full_day_leave', 'half_day_leave']:
            with col1:
                st.markdown('<div class="neon-card">', unsafe_allow_html=True)
                st.markdown('<h4 style="color: #6ee7b7; margin-bottom: 1rem;">🌱 Recovery Activities</h4>', unsafe_allow_html=True)
                for item in analysis.get('leave_activities', []):
                    st.markdown(f'<div class="recommendation-pill pill-positive">{item}</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
                
            with col2:
                st.markdown('<div class="neon-card">', unsafe_allow_html=True)
                st.markdown('<h4 style="color: #fca5a5; margin-bottom: 1rem;">❌ Avoid During Leave</h4>', unsafe_allow_html=True)
                for item in analysis.get('leave_avoid', []):
                    st.markdown(f'<div class="recommendation-pill pill-negative">{item}</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
        else:
            with col1:
                st.markdown('<div class="neon-card">', unsafe_allow_html=True)
                st.markdown('<h4 style="color: #6ee7b7; margin-bottom: 1rem;">💚 If Working Tomorrow</h4>', unsafe_allow_html=True)
                for item in analysis.get('work_activities', []):
                    st.markdown(f'<div class="recommendation-pill pill-positive">{item}</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
                
            with col2:
                st.markdown('<div class="neon-card">', unsafe_allow_html=True)
                st.markdown('<h4 style="color: #fca5a5; margin-bottom: 1rem;">❌ Avoid While Working</h4>', unsafe_allow_html=True)
                for item in analysis.get('work_avoid', []):
                    st.markdown(f'<div class="recommendation-pill pill-negative">{item}</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
        
        # Additional info
        if analysis.get('warning_signs'):
            st.markdown(f'''
            <div class="info-card">
                <div style="font-weight: 600; margin-bottom: 0.5rem; color: #fca5a5;">⚠️ Watch for these signs:</div>
                <div style="font-size: 0.9rem;">{' • '.join(analysis['warning_signs'])}</div>
            </div>
            ''', unsafe_allow_html=True)
        
        if analysis.get('recovery_estimate'):
            st.markdown(f'''
            <div class="info-card">
                <div style="font-weight: 600; margin-bottom: 0.5rem; color: #6ee7b7;">⏰ Recovery timeframe:</div>
                <div style="font-size: 0.9rem;">{analysis['recovery_estimate']}</div>
            </div>
            ''', unsafe_allow_html=True)
    
    # Footer
    st.markdown("---")
    st.markdown('''
    <div style="text-align: center; color: #64748b; font-size: 0.875rem; padding: 1.5rem 0;">
        <strong>Your wellbeing matters.</strong><br>
        This tool provides guidance, not medical advice. For serious concerns, consult a healthcare professional.
    </div>
    ''', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
