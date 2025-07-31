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

# Clean Apple-like CSS with visible fonts
st.markdown("""
<style>
    /* Force white background */
    .stApp {
        background-color: #ffffff !important;
    }
    .main .block-container {
        background-color: #ffffff !important;
        padding-top: 2rem;
    }
    
    /* Main title styling */
    .main-title {
        font-size: 2.5rem !important;
        font-weight: 600 !important;
        text-align: center !important;
        color: #000000 !important;
        margin-bottom: 0.5rem !important;
        font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", sans-serif !important;
    }
    
    /* Subtitle styling */
    .subtitle {
        font-size: 1.2rem !important;
        text-align: center !important;
        color: #666666 !important;
        margin-bottom: 3rem !important;
        font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", sans-serif !important;
    }
    
    /* Decision card */
    .decision-card {
        background: #007aff !important;
        border-radius: 16px !important;
        padding: 2rem !important;
        color: white !important;
        text-align: center !important;
        margin: 2rem 0 !important;
        box-shadow: 0 4px 20px rgba(0, 122, 255, 0.15) !important;
    }
    
    /* Recommendation boxes */
    .recommendation {
        background: #f8f9fa !important;
        border-radius: 12px !important;
        padding: 1.5rem !important;
        margin: 1rem 0 !important;
        color: #000000 !important;
        border: 1px solid #dee2e6 !important;
        font-weight: 500 !important;
    }
    
    /* Do items (green) */
    .do-item {
        background: #d4edda !important;
        border-radius: 8px !important;
        padding: 1rem !important;
        margin: 0.5rem 0 !important;
        color: #000000 !important;
        font-weight: 500 !important;
        border-left: 3px solid #28a745 !important;
    }
    
    /* Don't items (red) */
    .dont-item {
        background: #f8d7da !important;
        border-radius: 8px !important;
        padding: 1rem !important;
        margin: 0.5rem 0 !important;
        color: #000000 !important;
        font-weight: 500 !important;
        border-left: 3px solid #dc3545 !important;
    }
    
    /* Button styling */
    .stButton > button {
        width: 100% !important;
        background: #007aff !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 1rem !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        margin-top: 1.5rem !important;
        font-family: -apple-system, BlinkMacSystemFont, sans-serif !important;
    }
    
    /* Weather card */
    .weather-card {
        background: #f8f9fa !important;
        border-radius: 12px !important;
        padding: 1.5rem !important;
        margin: 1rem 0 !important;
        color: #000000 !important;
        text-align: center !important;
        border: 1px solid #dee2e6 !important;
    }
    
    /* Override all text to be visible */
    h1, h2, h3, h4, h5, h6, p, div, span, label {
        color: #000000 !important;
    }
    
    /* Streamlit specific overrides */
    .stMarkdown, .stText {
        color: #000000 !important;
    }
    
    /* Section headers */
    .main h3 {
        color: #000000 !important;
        font-weight: 600 !important;
        margin-bottom: 1rem !important;
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
    "wellness_score": 65,
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

def create_wellness_trend():
    """Create wellness trend visualization"""
    if len(st.session_state.assessments) < 2:
        return None
    
    df = pd.DataFrame(st.session_state.assessments[-14:])
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['wellness_score'],
        mode='lines+markers',
        line=dict(color='#74b9ff', width=3),
        marker=dict(size=10, color='#0984e3'),
        fill='tonexty',
        fillcolor='rgba(116, 185, 255, 0.2)'
    ))
    
    fig.update_layout(
        title="Your Wellness Journey",
        xaxis_title="Date",
        yaxis_title="Wellness Score",
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(family="-apple-system, BlinkMacSystemFont, sans-serif"),
        showlegend=False,
        height=350,
        yaxis=dict(range=[0, 100])
    )
    
    return fig

def main():
    # Header
    st.markdown('<h1 class="main-title">Should I Take Leave Tomorrow?</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">AI-powered decision making for your work-life balance</p>', unsafe_allow_html=True)
    
    # Get tomorrow's weather
    weather = get_weather_tomorrow()
    
    # Weather display
    st.markdown(f'''
    <div class="weather-card">
        <h3 style="margin: 0; color: #000000 !important; font-weight: 600;">Tomorrow's Weather</h3>
        <p style="font-size: 1.1rem; margin: 0.5rem 0; color: #000000 !important;">
            <strong>{weather['temp_high']}°C / {weather['temp_low']}°C</strong><br>
            {weather['condition']} • {weather['rain_chance']}% chance of rain
        </p>
    </div>
    ''', unsafe_allow_html=True)
    
    # Input section
    st.markdown("### How are you feeling today?")
    
    col1, col2 = st.columns(2)
    
    with col1:
        mood = st.selectbox(
            "Overall mood",
            ["Excellent", "Good", "Okay", "Struggling", "Overwhelmed", "Exhausted"],
            help="How would you describe your general state today?"
        )
        
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
    
    # Analysis button
    if st.button("Get My Personalized Recommendation", type="primary"):
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
            
            # Display results
            leave_type_map = {
                "full_day_leave": ("Take Full Day Off", "#e74c3c"),
                "half_day_leave": ("Take Half Day / Leave Early", "#f39c12"),
                "work_with_care": ("Work With Extra Self-Care", "#f1c40f"),
                "work_normally": ("Work Normally", "#27ae60")
            }
            
            decision_text, decision_color = leave_type_map.get(analysis['leave_type'], ("Work With Care", "#74b9ff"))
            
            st.markdown(f"""
            <div class="decision-card">
                <h2 style="margin: 0; font-weight: 600;">{decision_text}</h2>
                <p style="font-size: 1.1rem; opacity: 0.9; margin: 1rem 0;">{analysis['decision_summary']}</p>
                <p style="font-size: 0.9rem; opacity: 0.8;">Confidence: {analysis['confidence']}%</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Recommendations based on decision
            col1, col2 = st.columns(2)
            
            if analysis['leave_type'] in ['full_day_leave', 'half_day_leave']:
                with col1:
                    st.markdown("**Recovery Activities:**")
                    for item in analysis.get('leave_activities', []):
                        st.markdown(f'<div class="do-item">{item}</div>', unsafe_allow_html=True)
                
                with col2:
                    st.markdown("**Avoid During Leave:**")
                    for item in analysis.get('leave_avoid', []):
                        st.markdown(f'<div class="dont-item">{item}</div>', unsafe_allow_html=True)
            else:
                with col1:
                    st.markdown("**If You Work Tomorrow:**")
                    for item in analysis.get('work_activities', []):
                        st.markdown(f'<div class="do-item">{item}</div>', unsafe_allow_html=True)
                
                with col2:
                    st.markdown("**Avoid While Working:**")
                    for item in analysis.get('work_avoid', []):
                        st.markdown(f'<div class="dont-item">{item}</div>', unsafe_allow_html=True)
            
            if analysis.get('warning_signs'):
                st.markdown(f"""
                <div class="recommendation">
                    <strong>Watch for these warning signs:</strong><br>
                    {' • '.join(analysis['warning_signs'])}
                </div>
                """, unsafe_allow_html=True)
            
            # Recovery timeline
            if analysis.get('recovery_estimate'):
                st.markdown(f"""
                <div class="recommendation">
                    <strong>Expected recovery time:</strong> {analysis['recovery_estimate']}
                </div>
                """, unsafe_allow_html=True)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666666 !important; font-size: 0.9rem; padding: 1.5rem;">
        <strong>Your wellbeing matters.</strong> This tool provides guidance, not medical advice.<br>
        For serious mental health concerns, please consult a healthcare professional.
    </div>
    """, unsafe_allow_html=True)
