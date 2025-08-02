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

# Minimal modern CSS with soft gradients and clean typography
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    .stApp {
        background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    .main-container {
        max-width: 680px;
        margin: 0 auto;
        padding: 2rem 1rem;
    }
    
    .hero-section {
        text-align: center;
        margin-bottom: 3rem;
        padding: 2rem 0;
    }
    
    .main-title {
        font-size: 2.25rem;
        font-weight: 700;
        color: #0f172a;
        margin-bottom: 0.5rem;
        letter-spacing: -0.025em;
        line-height: 1.2;
    }
    
    .subtitle {
        font-size: 1rem;
        color: #64748b;
        margin-bottom: 0;
        font-weight: 400;
    }
    
    .glass-card {
        background: rgba(255, 255, 255, 0.8);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 16px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 4px 24px rgba(0, 0, 0, 0.06);
    }
    
    .weather-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .weather-icon {
        font-size: 2.5rem;
        margin: 0.5rem 0;
        filter: drop-shadow(0 2px 4px rgba(0,0,0,0.1));
    }
    
    .decision-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        text-align: center;
        margin: 2rem 0;
        padding: 2.5rem 2rem;
    }
    
    .decision-title {
        font-size: 1.5rem;
        font-weight: 600;
        margin-bottom: 1rem;
        text-shadow: 0 1px 2px rgba(0,0,0,0.1);
    }
    
    .pill-positive {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: white;
        border-radius: 24px;
        padding: 0.75rem 1.25rem;
        margin: 0.25rem;
        font-size: 0.875rem;
        font-weight: 500;
        border: none;
        box-shadow: 0 2px 8px rgba(16, 185, 129, 0.25);
    }
    
    .pill-negative {
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
        color: white;
        border-radius: 24px;
        padding: 0.75rem 1.25rem;
        margin: 0.25rem;
        font-size: 0.875rem;
        font-weight: 500;
        border: none;
        box-shadow: 0 2px 8px rgba(239, 68, 68, 0.25);
    }
    
    .info-card {
        background: rgba(255, 255, 255, 0.6);
        border: 1px solid rgba(148, 163, 184, 0.2);
        border-radius: 12px;
        padding: 1.25rem;
        margin: 1rem 0;
        color: #334155;
    }
    
    .section-title {
        font-size: 1.125rem;
        font-weight: 600;
        color: #0f172a;
        margin-bottom: 1rem;
        letter-spacing: -0.01em;
    }
    
    /* Streamlit component styling */
    .stSelectbox > div > div {
        background: rgba(255, 255, 255, 0.8);
        border: 1px solid rgba(148, 163, 184, 0.3);
        border-radius: 8px;
    }
    
    .stSlider > div > div {
        background: rgba(255, 255, 255, 0.8);
        border-radius: 8px;
    }
    
    .stButton > button {
        width: 100%;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.875rem 1.5rem;
        font-weight: 600;
        font-size: 1rem;
        margin-top: 1.5rem;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
        transition: all 0.2s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 6px 16px rgba(102, 126, 234, 0.4);
    }
    
    /* Labels styling */
    .stSelectbox label,
    .stSlider label,
    label[data-testid="stWidgetLabel"] {
        color: #374151 !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 500 !important;
        font-size: 0.875rem !important;
        margin-bottom: 0.5rem !important;
    }
    
    /* Animations */
    @keyframes gentle-float {
        0%, 100% { transform: translateY(0px); }
        50% { transform: translateY(-3px); }
    }
    
    @keyframes fade-in {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .floating-animation {
        animation: gentle-float 3s ease-in-out infinite;
    }
    
    .fade-in {
        animation: fade-in 0.6s ease-out;
    }
    
    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 6px;
    }
    
    ::-webkit-scrollbar-track {
        background: rgba(148, 163, 184, 0.1);
        border-radius: 3px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: rgba(148, 163, 184, 0.4);
        border-radius: 3px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: rgba(148, 163, 184, 0.6);
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

def get_weather_icon(condition):
    """Get appropriate weather icon and animation"""
    condition_lower = condition.lower()
    if 'rain' in condition_lower or 'shower' in condition_lower:
        return "🌧️"
    elif 'cloud' in condition_lower:
        return "☁️"
    elif 'sun' in condition_lower or 'clear' in condition_lower:
        return "☀️"
    else:
        return "🌤️"

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
    # Hero section
    st.markdown('''
    <div class="hero-section">
        <h1 class="main-title">Should I Take Leave Tomorrow?</h1>
        <p class="subtitle">AI-powered guidance for your work-life balance</p>
    </div>
    ''', unsafe_allow_html=True)
    
    # Get tomorrow's weather
    weather = get_weather_tomorrow()
    weather_icon = get_weather_icon(weather['condition'])
    
    # Weather card
    st.markdown(f'''
    <div class="glass-card weather-card">
        <h3 style="margin: 0 0 0.5rem 0; font-weight: 600; font-size: 1.125rem;">Tomorrow's Weather</h3>
        <div class="weather-icon floating-animation">{weather_icon}</div>
        <div style="font-size: 1.125rem; font-weight: 600; margin-bottom: 0.25rem;">
            {weather['temp_high']}°C / {weather['temp_low']}°C
        </div>
        <div style="opacity: 0.9; font-size: 0.9rem;">
            {weather['condition']} • {weather['rain_chance']}% chance of rain
        </div>
    </div>
    ''', unsafe_allow_html=True)
    
    # Input section
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown('<h3 class="section-title">How are you feeling today?</h3>', unsafe_allow_html=True)
    
    # Create a more minimal form layout
    col1, col2 = st.columns([1, 1], gap="medium")
    
    with col1:
        mood = st.selectbox(
            "Overall mood",
            ["Excellent", "Good", "Okay", "Struggling", "Overwhelmed", "Exhausted"],
            help="How would you describe your general state today?"
        )
        
        energy = st.slider("Energy level", 1, 10, 5, help="1 = Completely drained, 10 = Highly energized")
        stress = st.slider("Current stress", 1, 10, 5, help="1 = Very relaxed, 10 = Extremely stressed")
        
    with col2:
        sleep = st.slider("Sleep quality", 1, 10, 6, help="1 = Terrible, 10 = Perfect rest")
        work_pressure = st.slider("Work pressure", 1, 10, 5, help="1 = Very light, 10 = Overwhelming")
        personal_stress = st.slider("Personal stress", 1, 10, 4, help="1 = Very peaceful, 10 = Major issues")
    
    # Additional inputs in a cleaner layout
    st.markdown('<div style="margin-top: 1.5rem;">', unsafe_allow_html=True)
    
    col3, col4 = st.columns(2)
    with col3:
        physical_symptoms = st.selectbox(
            "Physical symptoms",
            ["None", "Mild tension/headache", "Moderate discomfort", "Severe symptoms"]
        )
        
        last_break = st.selectbox(
            "Last day off",
            ["Within last month", "1-2 months ago", "2-6 months ago", "6+ months ago", "Never"]
        )
    
    with col4:
        tomorrow_importance = st.selectbox(
            "Tomorrow's work priority",
            ["Low - routine tasks", "Medium - some important items", "High - major deadlines", "Critical - cannot be postponed"]
        )
        
        support = st.selectbox(
            "Support system",
            ["Strong support network", "Good support", "Limited support", "Feeling isolated"]
        )
    
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Analysis button
    if st.button("✨ Get My Personalized Recommendation", type="primary"):
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
        
        with st.spinner("Analyzing your situation..."):
            time.sleep(1.5)
            analysis = analyze_leave_decision(data, weather)
            
            # Save assessment
            entry = {
                **data,
                'date': datetime.now().strftime('%Y-%m-%d'),
                'wellness_score': analysis['wellness_score'],
                'recommendation': analysis['leave_type']
            }
            st.session_state.assessments.insert(0, entry)
            st.session_state.assessments = st.session_state.assessments[:30]
            
            # Display results with fade-in animation
            leave_type_map = {
                "full_day_leave": "Take Full Day Off",
                "half_day_leave": "Take Half Day / Leave Early", 
                "work_with_care": "Work With Extra Self-Care",
                "work_normally": "Work Normally"
            }
            
            decision_text = leave_type_map.get(analysis['leave_type'], "Work With Care")
            
            # Decision card
            st.markdown(f'''
            <div class="glass-card decision-card fade-in">
                <div class="decision-title">{decision_text}</div>
                <p style="font-size: 1rem; opacity: 0.95; margin: 0.5rem 0; line-height: 1.5;">{analysis['decision_summary']}</p>
                <div style="font-size: 0.875rem; opacity: 0.8; margin-top: 1rem;">
                    Wellness Score: {analysis['wellness_score']}/100 • Confidence: {analysis['confidence']}%
                </div>
            </div>
            ''', unsafe_allow_html=True)
            
            # Recommendations in minimal cards
            col1, col2 = st.columns(2, gap="medium")
            
            if analysis['leave_type'] in ['full_day_leave', 'half_day_leave']:
                with col1:
                    st.markdown('<div class="glass-card fade-in">', unsafe_allow_html=True)
                    st.markdown('<div class="section-title">💚 Recovery Activities</div>', unsafe_allow_html=True)
                    for item in analysis.get('leave_activities', []):
                        st.markdown(f'<div class="pill-positive">{item}</div>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                
                with col2:
                    st.markdown('<div class="glass-card fade-in">', unsafe_allow_html=True)
                    st.markdown('<div class="section-title">❌ Avoid During Leave</div>', unsafe_allow_html=True)
                    for item in analysis.get('leave_avoid', []):
                        st.markdown(f'<div class="pill-negative">{item}</div>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
            else:
                with col1:
                    st.markdown('<div class="glass-card fade-in">', unsafe_allow_html=True)
                    st.markdown('<div class="section-title">💚 If Working Tomorrow</div>', unsafe_allow_html=True)
                    for item in analysis.get('work_activities', []):
                        st.markdown(f'<div class="pill-positive">{item}</div>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                
                with col2:
                    st.markdown('<div class="glass-card fade-in">', unsafe_allow_html=True)
                    st.markdown('<div class="section-title">❌ Avoid While Working</div>', unsafe_allow_html=True)
                    for item in analysis.get('work_avoid', []):
                        st.markdown(f'<div class="pill-negative">{item}</div>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
            
            # Additional info cards
            if analysis.get('warning_signs'):
                st.markdown(f'''
                <div class="info-card fade-in">
                    <div style="font-weight: 600; margin-bottom: 0.5rem; color: #dc2626;">⚠️ Watch for these signs:</div>
                    <div style="font-size: 0.9rem; line-height: 1.4;">{' • '.join(analysis['warning_signs'])}</div>
                </div>
                ''', unsafe_allow_html=True)
            
            if analysis.get('recovery_estimate'):
                st.markdown(f'''
                <div class="info-card fade-in">
                    <div style="font-weight: 600; margin-bottom: 0.5rem; color: #059669;">⏰ Recovery timeframe:</div>
                    <div style="font-size: 0.9rem;">{analysis['recovery_estimate']}</div>
                </div>
                ''', unsafe_allow_html=True)
    
    # Minimal footer
    st.markdown("---")
    st.markdown('''
    <div style="text-align: center; color: #64748b; font-size: 0.875rem; padding: 1.5rem 0; line-height: 1.6;">
        <strong>Your wellbeing matters.</strong><br>
        This tool provides guidance, not medical advice. For serious concerns, consult a healthcare professional.
    </div>
    ''', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
