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
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
    
    .stApp {
        background: linear-gradient(135deg, #0f0f23 0%, #1a1a2e 50%, #16213e 100%);
        font-family: 'Space Grotesk', sans-serif;
        color: #e2e8f0;
    }
    
    /* Animated background particles */
    .stApp::before {
        content: '';
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-image: 
            radial-gradient(circle at 25% 25%, rgba(120, 119, 198, 0.3) 0%, transparent 50%),
            radial-gradient(circle at 75% 75%, rgba(255, 119, 198, 0.2) 0%, transparent 50%),
            radial-gradient(circle at 50% 50%, rgba(119, 198, 255, 0.1) 0%, transparent 50%);
        animation: particleFloat 20s ease-in-out infinite;
        pointer-events: none;
        z-index: -1;
    }
    
    @keyframes particleFloat {
        0%, 100% { transform: translateY(0px) rotate(0deg); }
        33% { transform: translateY(-20px) rotate(120deg); }
        66% { transform: translateY(10px) rotate(240deg); }
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
        text-shadow: 0 0 30px rgba(102, 126, 234, 0.5);
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
        background: rgba(30, 41, 59, 0.8);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(148, 163, 184, 0.2);
        border-radius: 20px;
        padding: 2rem;
        margin: 1.5rem 0;
        box-shadow: 
            0 8px 32px rgba(0, 0, 0, 0.3),
            inset 0 1px 0 rgba(255, 255, 255, 0.1);
        position: relative;
        overflow: hidden;
    }
    
    .neon-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.1), transparent);
        animation: shimmer 3s infinite;
    }
    
    @keyframes shimmer {
        0% { left: -100%; }
        100% { left: 100%; }
    }
    
    .weather-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        text-align: center;
        position: relative;
        overflow: hidden;
    }
    
    .weather-card::after {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: conic-gradient(from 0deg, transparent, rgba(255, 255, 255, 0.1), transparent);
        animation: rotate 10s linear infinite;
        pointer-events: none;
    }
    
    @keyframes rotate {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    .decision-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        text-align: center;
        margin: 2rem 0;
        position: relative;
        overflow: hidden;
    }
    
    .decision-card::before {
        content: '';
        position: absolute;
        top: -2px;
        left: -2px;
        right: -2px;
        bottom: -2px;
        background: linear-gradient(45deg, #ff006e, #8338ec, #3a86ff, #06ffa5, #ffbe0b, #ff006e);
        border-radius: inherit;
        animation: borderGlow 3s linear infinite;
        z-index: -1;
    }
    
    @keyframes borderGlow {
        0% { background-position: 0% 50%; }
        100% { background-position: 200% 50%; }
    }
    
    .wellness-meter {
        background: rgba(15, 23, 42, 0.8);
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1rem 0;
        border: 1px solid rgba(59, 130, 246, 0.3);
        position: relative;
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
        cursor: default;
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
        position: relative;
        overflow: hidden;
    }
    
    .stButton > button:hover {
        transform: translateY(-3px);
        box-shadow: 0 12px 35px rgba(102, 126, 234, 0.6);
    }
    
    .stButton > button::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
        transition: left 0.5s;
    }
    
    .stButton > button:hover::before {
        left: 100%;
    }
    
    /* Streamlit component styling */
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
    
    /* Progress indicator */
    .progress-dots {
        display: flex;
        justify-content: center;
        gap: 10px;
        margin: 2rem 0;
    }
    
    .dot {
        width: 12px;
        height: 12px;
        border-radius: 50%;
        background: rgba(59, 130, 246, 0.3);
        animation: pulse 2s infinite;
    }
    
    .dot.active {
        background: #3b82f6;
        box-shadow: 0 0 20px rgba(59, 130, 246, 0.8);
    }
    
    @keyframes pulse {
        0% { opacity: 0.4; }
        50% { opacity: 1; }
        100% { opacity: 0.4; }
    }
    
    /* AI thinking animation */
    .ai-thinking {
        display: inline-flex;
        align-items: center;
        gap: 5px;
        color: #8b5cf6;
        font-weight: 500;
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
    
    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: rgba(15, 23, 42, 0.8);
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, #667eea, #764ba2);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(135deg, #764ba2, #667eea);
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'assessments' not in st.session_state:
    st.session_state.assessments = []
if 'step' not in st.session_state:
    st.session_state.step = 0

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
    color = "red" if score < 40 else "orange" if score < 70 else "green"
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

DECISION FRAMEWORK:
- Full Day Leave: For burnout, severe stress, or mental health crisis
- Half Day/Early Leave: For moderate stress with manageable work
- Work Normally: For good mental state with support strategies
- Consider weather impact on mood and recovery opportunities

Respond in this EXACT JSON format (ensure valid JSON):
{{
    "wellness_score": 45,
    "leave_type": "full_day_leave",
    "confidence": 82,
    "main_reason": "Primary reason for recommendation",
    "decision_summary": "Brief 2-sentence explanation of the decision",
    "work_activities": ["3 things to do if working"],
    "work_avoid": ["3 things to avoid if working"],
    "leave_activities": ["4 recovery activities for leave day"],
    "leave_avoid": ["3 things to avoid during leave"],
    "warning_signs": ["signs requiring immediate attention"],
    "recovery_estimate": "Expected recovery timeframe"
}}

Leave types: "full_day_leave", "half_day_leave", "work_with_care", "work_normally"

SCORING GUIDE:
- 80-100: Excellent state, work normally
- 60-79: Good state, minor support needed
- 40-59: Moderate stress, consider half day
- 20-39: High stress, likely needs full day
- 0-19: Crisis level, definitely needs leave

Weather considerations:
- Rainy/gloomy: May worsen mood, indoor recovery activities
- Sunny/pleasant: Good for outdoor recovery, mood boost
- Extreme weather: Affects commute stress and recovery options"""

    try:
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        # Clean up the response text
        if response_text.startswith('```json'):
            response_text = response_text.replace('```json', '').replace('```', '').strip()
        
        result = json.loads(response_text)
        
        # Validate required fields
        required_fields = ['wellness_score', 'leave_type', 'confidence', 'main_reason', 'decision_summary']
        for field in required_fields:
            if field not in result:
                raise ValueError(f"Missing required field: {field}")
        
        return result
        
    except Exception as e:
        st.warning(f"AI analysis failed, using fallback logic: {str(e)}")
        
        # Enhanced fallback logic
        stress_factor = (data['stress'] + data['work_pressure'] + data['personal_stress']) / 3
        energy_factor = data['energy']
        sleep_factor = data['sleep']
        
        # Calculate wellness score
        wellness = 100 - (stress_factor * 10) - ((10 - energy_factor) * 8) - ((10 - sleep_factor) * 6)
        wellness = max(5, min(100, int(wellness)))
        
        # Decision logic based on multiple factors
        if wellness < 25 or (stress_factor > 8 and energy_factor < 3):
            leave_type = "full_day_leave"
            decision = "Your stress levels are critically high and energy is depleted. A full day of rest is essential to prevent burnout."
        elif wellness < 45 or (stress_factor > 6 and sleep_factor < 5):
            leave_type = "half_day_leave"
            decision = "Moderate stress levels suggest you need some recovery time. Consider taking half day or leaving early."
        elif wellness < 65:
            leave_type = "work_with_care"
            decision = "You can work tomorrow but need to be very careful with your energy and stress management."
        else:
            leave_type = "work_normally"
            decision = "You're in good shape to work tomorrow. Focus on maintaining your current positive state."
        
        return {
            "wellness_score": wellness,
            "leave_type": leave_type,
            "confidence": 75,
            "main_reason": f"Stress level {stress_factor:.1f}/10, Energy {energy_factor}/10",
            "decision_summary": decision,
            "work_activities": ["Take regular breaks every hour", "Prioritize only essential tasks", "Stay hydrated and eat well"],
            "work_avoid": ["Overtime or extra commitments", "Perfectionism on minor tasks", "Skipping lunch break"],
            "leave_activities": ["Sleep until naturally awake", "Light exercise or walk", "Do something you enjoy", "Connect with supportive people"],
            "leave_avoid": ["Checking work emails", "Intensive physical activities", "Making major decisions"],
            "warning_signs": ["Panic attacks", "Complete inability to focus", "Persistent physical symptoms"],
            "recovery_estimate": "1-3 days with proper rest"
        }

def main():
    # Animated header
    st.markdown('''
    <h1 class="main-title">Should I Take Leave Tomorrow?</h1>
    <p class="subtitle">✨ AI-powered decision making for your work-life balance</p>
    ''', unsafe_allow_html=True)
    
    # Progress indicator
    st.markdown('''
    <div class="progress-dots">
        <div class="dot active"></div>
        <div class="dot"></div>
        <div class="dot"></div>
    </div>
    ''', unsafe_allow_html=True)
    
    # Get tomorrow's weather
    weather = get_weather_tomorrow()
    
    # Weather display with rotating border animation
    weather_condition_lower = weather['condition'].lower()
    if 'rain' in weather_condition_lower or 'shower' in weather_condition_lower:
        weather_icon = "🌧️"
    elif 'cloud' in weather_condition_lower:
        weather_icon = "☁️"
    elif 'sun' in weather_condition_lower or 'clear' in weather_condition_lower:
        weather_icon = "☀️"
    else:
        weather_icon = "🌤️"
    
    st.markdown(f'''
    <div class="neon-card weather-card">
        <h3 style="margin: 0 0 1rem 0; font-weight: 600; z-index: 2; position: relative;">Tomorrow's Weather</h3>
        <div style="font-size: 3rem; margin: 1rem 0; z-index: 2; position: relative;">{weather_icon}</div>
        <div style="font-size: 1.3rem; font-weight: 600; margin: 0.5rem 0; z-index: 2; position: relative;">
            {weather['temp_high']}°C / {weather['temp_low']}°C
        </div>
        <div style="opacity: 0.9; font-size: 1rem; z-index: 2; position: relative;">
            {weather['condition']} • {weather['rain_chance']}% chance of rain
        </div>
    </div>
    ''', unsafe_allow_html=True)
    
    # Input section with neon cards
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
        
        energy = st.slider("Energy level", 1, 10, 5, help="1 = Completely drained, 10 = Highly energized")
        stress = st.slider("Current stress", 1, 10, 5, help="1 = Very relaxed, 10 = Extremely stressed")
        sleep = st.slider("Last night's sleep quality", 1, 10, 6, help="1 = Terrible, 10 = Perfect rest")
        
    with col2:
        work_pressure = st.slider("Work pressure level", 1, 10, 5, help="1 = Very light, 10 = Overwhelming")
        personal_stress = st.slider("Personal life stress", 1, 10, 4, help="1 = Very peaceful, 10 = Major issues")
        
        physical_symptoms = st.selectbox(
            "Physical symptoms",
            ["None", "Mild tension/headache", "Moderate discomfort", "Severe symptoms"]
        )
        
        last_break = st.selectbox(
            "When did you last take a day off?",
            ["Never", "6+ months ago", "2-6 months ago", "1-2 months ago", "Within last month"]
        )
    
    tomorrow_importance = st.selectbox(
        "How critical is tomorrow's work?",
        ["Low priority - routine tasks", "Medium - some important items", "High - major deadlines", "Critical - cannot be postponed"]
    )
    
    support = st.selectbox(
        "Your support system",
        ["Strong - great family/friend support", "Good - some supportive people", "Limited - few people to talk to", "Weak - feeling quite isolated"]
    )
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Analysis button with hover effects
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
        
        # Save assessment
        entry = {
            **data,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'wellness_score': analysis['wellness_score'],
            'recommendation': analysis['leave_type']
        }
        st.session_state.assessments.insert(0, entry)
        st.session_state.assessments = st.session_state.assessments[:30]
        
        # Wellness meter
        st.markdown(create_wellness_meter(analysis['wellness_score']), unsafe_allow_html=True)
        
        # Display results with animated border
        leave_type_map = {
            "full_day_leave": ("🏠 Take Full Day Off", "🔴"),
            "half_day_leave": ("⏰ Take Half Day / Leave Early", "🟡"),
            "work_with_care": ("⚠️ Work With Extra Self-Care", "🟠"),
            "work_normally": ("💼 Work Normally", "🟢")
        }
        
        decision_text, status_icon = leave_type_map.get(analysis['leave_type'], ("Work With Care", "🟡"))
        
        # Decision card with glowing border
        st.markdown(f'''
        <div class="neon-card decision-card">
            <h2 style="margin: 0; font-weight: 700; font-size: 1.8rem; z-index: 2; position: relative;">{decision_text}</h2>
            <div style="font-size: 2rem; margin: 1rem 0; z-index: 2; position: relative;">{status_icon}</div>
            <p style="font-size: 1.1rem; opacity: 0.95; margin: 1rem 0; line-height: 1.6; z-index: 2; position: relative;">{analysis['decision_summary']}</p>
            <div style="font-size: 0.9rem; opacity: 0.8; margin-top: 1.5rem; z-index: 2; position: relative;">
                Confidence: {analysis['confidence']}% | Reason: {analysis['main_reason']}
            </div>
        </div>
        ''', unsafe_allow_html=True)
        
        # Recommendations with hover effects
        col1, col2 = st.columns(2)
        
        if analysis['leave_type'] in ['full_day_leave', 'half_day_leave']:
            with col1:
                st.markdown('<div class="neon-card">', unsafe_allow_html=True)
                st.markdown('<h4 style="color: #6ee7b7; margin-bottom: 1rem;">🌱 Recovery Activities</h4>', unsafe_allow_html=True)
                for item in analysis.get('leave_activities', []):
                    st.markdown(f'<div class="recommendation-pill pill-positive">{item}</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
