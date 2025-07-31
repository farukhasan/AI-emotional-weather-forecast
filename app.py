import streamlit as st
import google.generativeai as genai
import sqlite3
import pandas as pd
import plotly.express as px
import requests
from datetime import datetime, timedelta
import json

# Page config with minimalistic design
st.set_page_config(
    page_title="MoodCast",
    page_icon="🌤️",
    layout="centered",  # Changed to centered for cleaner look
    initial_sidebar_state="collapsed"
)

# Initialize session state
if 'mood_history' not in st.session_state:
    st.session_state.mood_history = []
if 'current_forecast' not in st.session_state:
    st.session_state.current_forecast = None

# API Keys
try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
    WEATHER_API_KEY = st.secrets.get("PIRATE_WEATHER_API_KEY", "")
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-pro')
except:
    st.error("⚠️ Please add your API keys to Streamlit secrets!")
    st.stop()

# Custom CSS for minimalistic design
st.markdown("""
<style>
    /* Main container styling */
    .main-container {
        max-width: 800px;
        margin: 0 auto;
        padding: 1rem;
    }
    
    /* Card styling */
    .card {
        background: linear-gradient(135deg, #f5f7fa 0%, #e4e8f0 100%);
        border-radius: 15px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        transition: transform 0.3s ease;
    }
    
    .card:hover {
        transform: translateY(-5px);
    }
    
    /* Forecast card styling */
    .forecast-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 15px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        text-align: center;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
    }
    
    /* Input styling */
    .stTextInput, .stSelectbox, .stSlider, .stNumberInput {
        margin-bottom: 1rem;
    }
    
    /* Button styling */
    .stButton button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1.5rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(0,0,0,0.1);
    }
    
    /* Section headers */
    .section-header {
        font-size: 1.2rem;
        font-weight: 600;
        margin-bottom: 1rem;
        color: #333;
        display: flex;
        align-items: center;
    }
    
    .section-header .icon {
        margin-right: 0.5rem;
    }
    
    /* Footer styling */
    .footer {
        text-align: center;
        margin-top: 2rem;
        padding: 1rem;
        color: #666;
        font-size: 0.9rem;
    }
    
    /* Mood selection styling */
    .mood-options {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
        margin-bottom: 1rem;
    }
    
    .mood-option {
        background: white;
        border: 2px solid #e0e0e0;
        border-radius: 10px;
        padding: 0.5rem 1rem;
        cursor: pointer;
        transition: all 0.2s ease;
        font-size: 0.9rem;
    }
    
    .mood-option:hover {
        border-color: #667eea;
    }
    
    .mood-option.selected {
        background: #667eea;
        color: white;
        border-color: #667eea;
    }
    
    /* Forecast item styling */
    .forecast-item {
        background: white;
        border-radius: 10px;
        padding: 1rem;
        margin-bottom: 0.8rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    
    .forecast-item-title {
        font-weight: 600;
        margin-bottom: 0.5rem;
        display: flex;
        align-items: center;
    }
    
    .forecast-item-title .icon {
        margin-right: 0.5rem;
    }
    
    /* Chart container */
    .chart-container {
        background: white;
        border-radius: 15px;
        padding: 1.5rem;
        margin-top: 1.5rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
    }
</style>
""", unsafe_allow_html=True)

def get_weather_data(lat=23.8103, lon=90.4125):
    """Get real weather data using Pirate Weather API"""
    if not WEATHER_API_KEY:
        return {
            "condition": "partly_cloudy_day", 
            "temp": 28, 
            "temp_high": 32,
            "temp_low": 24,
            "humidity": 75, 
            "description": "Partly cloudy with gentle breeze",
            "feels_like": 31,
            "wind_speed": 12,
            "uv_index": 6
        }
    
    try:
        url = f"https://api.pirateweather.net/forecast/{WEATHER_API_KEY}/{lat},{lon}"
        response = requests.get(url, timeout=5)
        data = response.json()
        
        current = data["currently"]
        daily = data["daily"]["data"][0] if "daily" in data else {}
        
        return {
            "condition": current.get("icon", "clear-day").replace("-", "_"),
            "temp": round((current["temperature"] - 32) * 5/9),
            "temp_high": round((daily.get("temperatureHigh", current["temperature"]) - 32) * 5/9),
            "temp_low": round((daily.get("temperatureLow", current["temperature"]) - 32) * 5/9),
            "humidity": round(current["humidity"] * 100),
            "description": current.get("summary", "Clear conditions"),
            "feels_like": round((current.get("apparentTemperature", current["temperature"]) - 32) * 5/9),
            "wind_speed": round(current.get("windSpeed", 0) * 1.609),
            "uv_index": current.get("uvIndex", 0)
        }
    except Exception as e:
        print(f"Weather API error: {e}")
        return {
            "condition": "partly_cloudy_day", 
            "temp": 28, 
            "temp_high": 32,
            "temp_low": 24,
            "humidity": 75, 
            "description": "Partly cloudy conditions",
            "feels_like": 31,
            "wind_speed": 12,
            "uv_index": 6
        }

def generate_ai_forecast(mood_data, weather_data, mood_history):
    """Generate AI-powered emotional forecast with creative suggestions"""
    
    # Prepare context for AI
    history_summary = ""
    if mood_history:
        recent_moods = [f"{entry['date']}: {entry['mood']} (Energy: {entry['energy']}, Stability: {entry['stability']})" 
                       for entry in mood_history[-5:]]
        history_summary = f"Recent mood pattern: {'; '.join(recent_moods)}"
    
    prompt = f"""
    You are an advanced emotional wellness AI coach with expertise in psychology, productivity, and life coaching. 
    Analyze this person's current state and provide a highly personalized, creative emotional forecast with specific actionable suggestions.
    CURRENT PERSON'S STATE:
    - Mood: {mood_data['mood']}
    - Energy Level: {mood_data['energy']}/10
    - Emotional Stability: {mood_data['stability']}/10
    - Sleep Hours: {mood_data['sleep']}
    - Stress Level: {mood_data['stress']}/10
    - Profession: {mood_data.get('profession', 'Not specified')}
    - Relationship Status: {mood_data.get('relationship', 'Not specified')}
    - Today's Events: {mood_data.get('events', 'None specified')}
    - Current Challenges: {mood_data.get('challenges', 'None specified')}
    
    ENVIRONMENTAL CONTEXT:
    - Weather: {weather_data['condition']}, {weather_data['temp']}°C (feels like {weather_data['feels_like']}°C)
    - High/Low: {weather_data['temp_high']}°C / {weather_data['temp_low']}°C
    - Description: {weather_data['description']}
    - Humidity: {weather_data['humidity']}%, Wind: {weather_data['wind_speed']} km/h
    - UV Index: {weather_data['uv_index']}
    
    MOOD HISTORY:
    {history_summary}
    Provide a response in this JSON format with CREATIVE, SPECIFIC, and BOLD suggestions:
    {{
        "forecast_type": "sunny/cloudy/stormy/energetic/volcanic/serene",
        "confidence": "percentage like 87%",
        "weather_description": "Creative one-line emotional weather description",
        "emotional_temperature": "Like 'Emotional High: 8°C, Low: 3°C, RealFeel: 6°C'",
        "key_insights": ["Deep insight about their current state", "Pattern observation", "Hidden strength identified"],
        
        "professional_suggestions": [
            "Specific work-related advice based on their profession and current state",
            "Meeting/deadline management advice", 
            "Productivity timing recommendations",
            "Professional relationship advice"
        ],
        
        "personal_life_suggestions": [
            "Relationship advice (if applicable)",
            "Social interaction recommendations", 
            "Self-care activities",
            "Creative or fun activities based on energy/mood"
        ],
        
        "bold_decisions": [
            "Specific bold advice like 'Postpone that 3pm meeting - your focus will be scattered'",
            "Social recommendations like 'Call your partner for lunch - you need connection today'",
            "Life advice like 'Skip the gym today, do yoga instead - your body needs gentleness'"
        ],
        
        "optimal_timing": [
            "Best time for important decisions",
            "Peak energy windows",
            "Ideal time for social interactions",
            "When to avoid stressful activities"
        ],
        
        "weather_mood_connection": "How today's weather specifically affects their emotional state",
        
        "risk_factors": ["Specific things to watch out for today"],
        "power_moves": ["Things they should definitely do today to maximize their potential"]
    }}
    BE CREATIVE, SPECIFIC, and ACTIONABLE. Don't give generic advice - tailor everything to their profession, relationship status, current mood, and the weather. 
    Make bold suggestions that could genuinely improve their day. Consider their energy and stability levels carefully.
    """
    
    try:
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        if response_text.startswith('```json'):
            response_text = response_text[7:-3]
        elif response_text.startswith('```'):
            response_text = response_text[3:-3]
        
        forecast = json.loads(response_text)
        return forecast
    except Exception as e:
        st.error(f"AI Analysis Error: {e}")
        return {
            "forecast_type": "cloudy",
            "confidence": "75%",
            "weather_description": "Mixed emotional conditions with potential for clarity",
            "emotional_temperature": "Emotional High: 6°C, Low: 4°C, RealFeel: 5°C",
            "key_insights": ["Analysis temporarily unavailable", "Your patterns show resilience"],
            "professional_suggestions": ["Take regular breaks", "Focus on routine tasks"],
            "personal_life_suggestions": ["Connect with someone you care about", "Do something that brings you joy"],
            "bold_decisions": ["Trust your instincts today", "Don't overcommit your energy"],
            "optimal_timing": ["Morning hours may be best for focus"],
            "weather_mood_connection": "Weather conditions may be affecting your energy levels",
            "risk_factors": ["Monitor stress levels throughout the day"],
            "power_moves": ["One small act of self-care will compound positively"]
        }

def save_mood_entry(mood_data):
    """Save mood entry to session state"""
    entry = {
        **mood_data,
        'timestamp': datetime.now().isoformat(),
        'date': datetime.now().strftime('%Y-%m-%d')
    }
    st.session_state.mood_history.insert(0, entry)
    # Keep only last 30 entries
    st.session_state.mood_history = st.session_state.mood_history[:30]

def create_mood_trend_chart():
    """Create mood trend visualization"""
    if len(st.session_state.mood_history) < 2:
        return None
    
    df = pd.DataFrame(st.session_state.mood_history)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')
    
    # Calculate overall mood score
    df['mood_score'] = (df['energy'] + df['stability'] + (10 - df['stress'])) / 3
    df['energy_trend'] = df['energy']
    df['stability_trend'] = df['stability']
    
    fig = px.line(df, x='date', y=['mood_score', 'energy_trend', 'stability_trend'], 
                  title='Your Emotional Weather Trends',
                  labels={'value': 'Score (1-10)', 'date': 'Date', 'variable': 'Metric'},
                  color_discrete_map={
                      'mood_score': '#FF6B6B',
                      'energy_trend': '#4ECDC4', 
                      'stability_trend': '#45B7D1'
                  })
    fig.update_layout(height=400, legend=dict(orientation="h", yanchor="bottom", y=1.02))
    return fig

# Main App
def main():
    # Custom container for centered content
    with st.container():
        st.markdown('<div class="main-container">', unsafe_allow_html=True)
        
        # Header with minimalistic design
        st.markdown("""
        <div style="text-align: center; margin-bottom: 2rem;">
            <h1 style="font-size: 2.5rem; font-weight: 300; margin-bottom: 0.5rem;">🌤️ MoodCast</h1>
            <p style="font-size: 1.1rem; color: #666;">Your personal emotional weather forecast</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Get current weather
        weather_data = get_weather_data()
        
        # Main content in two columns
        col1, col2 = st.columns([1, 1])
        
        with col1:
            # Input card
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown('<div class="section-header"><span class="icon">📝</span> How are you feeling today?</div>', unsafe_allow_html=True)
            
            # Mood selection with visual options
            mood_options = {
                'energetic': '⚡ Energetic',
                'calm': '☁️ Calm', 
                'happy': '☀️ Happy',
                'anxious': '🌧️ Anxious',
                'tired': '🌙 Tired',
                'focused': '☕ Focused',
                'creative': '🎨 Creative',
                'overwhelmed': '🌪️ Overwhelmed'
            }
            
            # Create a grid of mood options
            selected_mood = st.selectbox(
                "Select your current mood", 
                options=list(mood_options.keys()),
                format_func=lambda x: mood_options[x],
                key="mood_select"
            )
            
            # Core metrics with sliders
            energy_level = st.slider("Energy Level", 1, 10, 5, key="energy")
            stability = st.slider("Emotional Stability", 1, 10, 5, key="stability")
            stress_level = st.slider("Stress Level", 1, 10, 3, key="stress")
            sleep_hours = st.number_input("Hours of sleep", 0.0, 12.0, 7.0, step=0.5, key="sleep")
            
            # Context information in an expander
            with st.expander("Add context (optional)", expanded=False):
                profession = st.selectbox("Your Profession", [
                    "Student", "Software Developer", "Teacher", "Healthcare Worker", 
                    "Manager/Executive", "Creative Professional", "Sales/Marketing", 
                    "Entrepreneur", "Consultant", "Engineer", "Freelancer", "Other"
                ], key="profession")
                
                relationship = st.selectbox("Relationship Status", [
                    "Single", "In a relationship", "Married", "It's complicated", "Prefer not to say"
                ], key="relationship")
                
                events = st.text_area("Today's events/schedule", 
                                     placeholder="e.g., Important presentation at 2pm, dinner date...", key="events")
                
                challenges = st.text_area("Current challenges", 
                                         placeholder="e.g., Deadline stress, relationship issues...", key="challenges")
            
            # Generate button with custom styling
            if st.button("🔮 Generate My Forecast", type="primary", key="generate_btn"):
                mood_data = {
                    'mood': selected_mood,
                    'energy': energy_level,
                    'stability': stability,
                    'sleep': sleep_hours,
                    'stress': stress_level,
                    'profession': profession,
                    'relationship': relationship,
                    'events': events,
                    'challenges': challenges
                }
                
                with st.spinner("🧠 Analyzing your emotional patterns..."):
                    forecast = generate_ai_forecast(mood_data, weather_data, st.session_state.mood_history)
                    save_mood_entry(mood_data)
                    st.session_state.current_forecast = forecast
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            # Forecast display
            if st.session_state.current_forecast:
                forecast = st.session_state.current_forecast
                
                # Weather icons mapping
                weather_icons = {
                    'sunny': '☀️',
                    'cloudy': '☁️', 
                    'stormy': '⛈️',
                    'energetic': '⚡',
                    'volcanic': '🌋',
                    'serene': '🌅'
                }
                
                icon = weather_icons.get(forecast['forecast_type'], '🌤️')
                
                # Main forecast card
                st.markdown(f"""
                <div class="forecast-card">
                    <h1 style="font-size: 3em; margin: 0;">{icon}</h1>
                    <h2 style="margin: 10px 0; font-weight: 300;">{forecast['weather_description']}</h2>
                    <p style="font-size: 1em; margin: 5px 0; opacity: 0.9;">{forecast.get('emotional_temperature', '')}</p>
                    <p style="font-size: 0.9em; margin: 5px 0; opacity: 0.8;">Confidence: {forecast['confidence']}</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Weather-mood connection
                if 'weather_mood_connection' in forecast:
                    st.markdown(f"""
                    <div class="forecast-item">
                        <div class="forecast-item-title"><span class="icon">🌡️</span> Weather Impact</div>
                        <p>{forecast['weather_mood_connection']}</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Key insights
                st.markdown('<div class="forecast-item">', unsafe_allow_html=True)
                st.markdown('<div class="forecast-item-title"><span class="icon">🔍</span> Key Insights</div>', unsafe_allow_html=True)
                for insight in forecast['key_insights']:
                    st.markdown(f"• {insight}")
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Professional suggestions
                if 'professional_suggestions' in forecast:
                    st.markdown('<div class="forecast-item">', unsafe_allow_html=True)
                    st.markdown('<div class="forecast-item-title"><span class="icon">💼</span> Professional Advice</div>', unsafe_allow_html=True)
                    for suggestion in forecast['professional_suggestions']:
                        st.markdown(f"• {suggestion}")
                    st.markdown('</div>', unsafe_allow_html=True)
                
                # Personal life suggestions
                if 'personal_life_suggestions' in forecast:
                    st.markdown('<div class="forecast-item">', unsafe_allow_html=True)
                    st.markdown('<div class="forecast-item-title"><span class="icon">❤️</span> Personal Life</div>', unsafe_allow_html=True)
                    for suggestion in forecast['personal_life_suggestions']:
                        st.markdown(f"• {suggestion}")
                    st.markdown('</div>', unsafe_allow_html=True)
                
                # Bold decisions
                if 'bold_decisions' in forecast:
                    st.markdown('<div class="forecast-item" style="background-color: #fff8e1;">', unsafe_allow_html=True)
                    st.markdown('<div class="forecast-item-title"><span class="icon">⚡</span> Bold Moves</div>', unsafe_allow_html=True)
                    for decision in forecast['bold_decisions']:
                        st.markdown(f"• {decision}")
                    st.markdown('</div>', unsafe_allow_html=True)
                
                # Optimal timing
                if 'optimal_timing' in forecast:
                    st.markdown('<div class="forecast-item">', unsafe_allow_html=True)
                    st.markdown('<div class="forecast-item-title"><span class="icon">⏰</span> Perfect Timing</div>', unsafe_allow_html=True)
                    for timing in forecast['optimal_timing']:
                        st.markdown(f"• {timing}")
                    st.markdown('</div>', unsafe_allow_html=True)
                
                # Power moves
                if 'power_moves' in forecast:
                    st.markdown('<div class="forecast-item" style="background-color: #e8f5e9;">', unsafe_allow_html=True)
                    st.markdown('<div class="forecast-item-title"><span class="icon">🚀</span> Power Moves</div>', unsafe_allow_html=True)
                    for move in forecast['power_moves']:
                        st.markdown(f"• {move}")
                    st.markdown('</div>', unsafe_allow_html=True)
                
                # Risk factors
                if forecast.get('risk_factors'):
                    st.markdown('<div class="forecast-item" style="background-color: #ffebee;">', unsafe_allow_html=True)
                    st.markdown('<div class="forecast-item-title"><span class="icon">⚠️</span> Watch Out For</div>', unsafe_allow_html=True)
                    for risk in forecast['risk_factors']:
                        st.markdown(f"• {risk}")
                    st.markdown('</div>', unsafe_allow_html=True)
            
            else:
                # Placeholder when no forecast is generated
                st.markdown('<div class="card" style="text-align: center; padding: 2rem;">', unsafe_allow_html=True)
                st.markdown("""
                <div style="font-size: 3rem; margin-bottom: 1rem;">✨</div>
                <h3>Your personalized forecast awaits</h3>
                <p style="color: #666; margin-top: 1rem;">Complete your check-in to receive AI-powered insights tailored to your emotional state.</p>
                """, unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
        
        # Mood trend chart
        if st.session_state.mood_history:
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            st.markdown('<div class="section-header"><span class="icon">📈</span> Your Emotional Trends</div>', unsafe_allow_html=True)
            chart = create_mood_trend_chart()
            if chart:
                st.plotly_chart(chart, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Footer
        st.markdown("""
        <div class="footer">
            <p>MoodCast — Your AI Emotional Weather Companion</p>
            <p style="font-size: 0.8rem; margin-top: 0.5rem;">For serious mental health concerns, please consult professionals</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
