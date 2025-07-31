import streamlit as st
import google.generativeai as genai
import sqlite3
import pandas as pd
import plotly.express as px
import requests
from datetime import datetime, timedelta
import json

# Page config
st.set_page_config(
    page_title="🌤️ MoodCast - Emotional Weather Forecast",
    page_icon="🌤️",
    layout="wide"
)

# Initialize session state
if 'mood_history' not in st.session_state:
    st.session_state.mood_history = []

# API Keys (use Streamlit secrets)
try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
    WEATHER_API_KEY = st.secrets.get("PIRATE_WEATHER_API_KEY", "")
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('models/gemini-1-5-flash')
except:
    st.error("⚠️ Please add your API keys to Streamlit secrets!")
    st.stop()

def get_weather_data(lat=23.8103, lon=90.4125):  # Default: Dhaka coordinates
    """Get real weather data using Pirate Weather API (free 20k calls/month)"""
    if not WEATHER_API_KEY:
        # Mock weather data with more details
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
        # Pirate Weather API endpoint
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
            "wind_speed": round(current.get("windSpeed", 0) * 1.609),  # mph to kmh
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
        # Enhanced fallback forecast
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
    """Save mood entry to session state (in production, use database)"""
    entry = {
        **mood_data,
        'timestamp': datetime.now().isoformat(),
        'date': datetime.now().strftime('%Y-%m-%d')
    }
    st.session_state.mood_history.insert(0, entry)
    # Keep only last 30 entries
    st.session_state.mood_history = st.session_state.mood_history[:30]

def create_mood_trend_chart():
    """Create enhanced mood trend visualization"""
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
    st.title("🌤️ MoodCast - Your Emotional Weather Forecast")
    st.markdown("*AI-powered insights for your daily emotional climate*")
    
    # Get current weather
    weather_data = get_weather_data()
    
    # Enhanced sidebar with detailed weather
    with st.sidebar:
        st.header("🌍 Environmental Context")
        
        # Weather overview
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Current", f"{weather_data['temp']}°C")
            st.metric("High", f"{weather_data['temp_high']}°C")
        with col2:
            st.metric("Feels Like", f"{weather_data['feels_like']}°C")
            st.metric("Low", f"{weather_data['temp_low']}°C")
        
        st.metric("Humidity", f"{weather_data['humidity']}%")
        st.metric("Wind", f"{weather_data['wind_speed']} km/h")
        st.metric("UV Index", weather_data['uv_index'])
        
        st.markdown(f"**Conditions:** {weather_data['description']}")
        
        if st.session_state.mood_history:
            st.header("📊 Quick Stats")
            recent_entry = st.session_state.mood_history[0]
            st.metric("Last Check-in", recent_entry['date'])
            weekly_entries = len([e for e in st.session_state.mood_history 
                                if datetime.fromisoformat(e['timestamp']).date() >= 
                                (datetime.now() - timedelta(days=7)).date()])
            st.metric("This Week", f"{weekly_entries} check-ins")
    
    # Main content in two columns
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.header("📝 Today's Check-in")
        
        # Enhanced mood selection
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
        
        current_mood = st.selectbox("How are you feeling right now?", 
                                   options=list(mood_options.keys()),
                                   format_func=lambda x: mood_options[x])
        
        # Core metrics
        energy_level = st.slider("Energy Level", 1, 10, 5, 
                                help="1=Completely drained, 10=Highly energized")
        
        stability = st.slider("Emotional Stability", 1, 10, 5,
                             help="1=Very shaky/volatile, 10=Rock solid/steady")
        
        sleep_hours = st.number_input("Hours of sleep last night", 0.0, 12.0, 7.0, step=0.5)
        
        stress_level = st.slider("Current Stress Level", 1, 10, 3,
                                help="1=Very relaxed, 10=Extremely stressed")
        
        # New enhanced fields
        st.markdown("### 👤 Personal Context")
        
        profession = st.selectbox("Your Profession", [
            "Student", "Software Developer", "Teacher", "Healthcare Worker", 
            "Manager/Executive", "Creative Professional", "Sales/Marketing", 
            "Entrepreneur", "Consultant", "Engineer", "Freelancer", "Other"
        ])
        
        relationship = st.selectbox("Relationship Status", [
            "Single", "In a relationship", "Married", "It's complicated", "Prefer not to say"
        ])
        
        events = st.text_area("Today's events/schedule", 
                             placeholder="e.g., Important presentation at 2pm, dinner date, team meeting...")
        
        challenges = st.text_area("Current challenges/concerns", 
                                 placeholder="e.g., Deadline stress, relationship issues, health concerns...")
        
        # Generate forecast button
        if st.button("🔮 Generate My Emotional Forecast", type="primary", use_container_width=True):
            mood_data = {
                'mood': current_mood,
                'energy': energy_level,
                'stability': stability,
                'sleep': sleep_hours,
                'stress': stress_level,
                'profession': profession,
                'relationship': relationship,
                'events': events,
                'challenges': challenges
            }
            
            with st.spinner("🧠 AI is analyzing your emotional patterns..."):
                forecast = generate_ai_forecast(mood_data, weather_data, st.session_state.mood_history)
                save_mood_entry(mood_data)
                st.session_state.current_forecast = forecast
    
    with col2:
        st.header("🌤️ Your Personalized Forecast")
        
        if 'current_forecast' in st.session_state:
            forecast = st.session_state.current_forecast
            
            # Enhanced weather icon mapping
            weather_icons = {
                'sunny': '☀️',
                'cloudy': '☁️', 
                'stormy': '⛈️',
                'energetic': '⚡',
                'volcanic': '🌋',
                'serene': '🌅'
            }
            
            icon = weather_icons.get(forecast['forecast_type'], '🌤️')
            
            # Enhanced forecast display
            st.markdown(f"""
            <div style="text-align: center; padding: 25px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 20px; color: white; margin: 15px 0; box-shadow: 0 8px 32px rgba(0,0,0,0.1);">
                <h1 style="font-size: 4em; margin: 0; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);">{icon}</h1>
                <h2 style="margin: 15px 0; font-weight: 300;">{forecast['weather_description']}</h2>
                <p style="font-size: 1.1em; margin: 5px 0;">Confidence: {forecast['confidence']}</p>
                <p style="font-size: 0.9em; margin: 5px 0; opacity: 0.9;">{forecast.get('emotional_temperature', '')}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Weather-Mood Connection
            if 'weather_mood_connection' in forecast:
                st.info(f"🌡️ **Weather Impact:** {forecast['weather_mood_connection']}")
            
            # Key insights with enhanced styling
            st.markdown("### 🔍 **Key Insights About You Today**")
            for insight in forecast['key_insights']:
                st.success(f"💡 {insight}")
            
            # Professional suggestions
            if 'professional_suggestions' in forecast:
                st.markdown("### 💼 **Professional Recommendations**")
                for suggestion in forecast['professional_suggestions']:
                    st.info(f"🎯 {suggestion}")
            
            # Personal life suggestions
            if 'personal_life_suggestions' in forecast:
                st.markdown("### ❤️ **Personal Life Suggestions**")
                for suggestion in forecast['personal_life_suggestions']:
                    st.success(f"🌟 {suggestion}")
            
            # Bold decisions - highlighted
            if 'bold_decisions' in forecast:
                st.markdown("### ⚡ **Bold Moves for Today**")
                for decision in forecast['bold_decisions']:
                    st.warning(f"🎯 **{decision}**")
            
            # Optimal timing
            if 'optimal_timing' in forecast:
                st.markdown("### ⏰ **Perfect Timing**")
                for timing in forecast['optimal_timing']:
                    st.info(f"🕐 {timing}")
            
            # Power moves
            if 'power_moves' in forecast:
                st.markdown("### 🚀 **Today's Power Moves**")
                for move in forecast['power_moves']:
                    st.success(f"💪 {move}")
            
            # Risk factors
            if forecast.get('risk_factors'):
                st.markdown("### ⚠️ **Watch Out For**")
                for risk in forecast['risk_factors']:
                    st.error(f"🚨 {risk}")
        
        else:
            st.info("✨ Complete your detailed check-in to receive your personalized emotional forecast with creative suggestions!")
            st.markdown("**You'll get:**")
            st.markdown("- 🎯 Bold decision recommendations")
            st.markdown("- 💼 Professional advice tailored to your career")  
            st.markdown("- ❤️ Personal life suggestions")
            st.markdown("- ⏰ Optimal timing for activities")
            st.markdown("- 🌡️ Weather-emotion insights")
    
    # Enhanced mood trend chart
    if st.session_state.mood_history:
        st.markdown("---")
        st.header("📈 Your Emotional Weather Trends")
        chart = create_mood_trend_chart()
        if chart:
            st.plotly_chart(chart, use_container_width=True)
        
        # Enhanced recent history
        with st.expander("📋 Recent Check-ins & Patterns"):
            df = pd.DataFrame(st.session_state.mood_history[:10])
            if not df.empty:
                display_df = df[['date', 'mood', 'energy', 'stability', 'stress', 'profession']].copy()
                display_df.columns = ['Date', 'Mood', 'Energy', 'Stability', 'Stress', 'Profession']
                st.dataframe(display_df, use_container_width=True)
                
                # Quick stats
                avg_energy = df['energy'].mean()
                avg_stability = df['stability'].mean()
                st.markdown(f"**Recent Averages:** Energy: {avg_energy:.1f}/10 | Stability: {avg_stability:.1f}/10")

if __name__ == "__main__":
    main()

# Enhanced footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; padding: 20px; color: #666;">
    <p>🌟 <strong>MoodCast</strong> - Your AI Emotional Weather Companion</p>
    <p><em>Remember: This is a wellness tool designed to enhance self-awareness. For serious mental health concerns, please consult professionals.</em></p>
    <p>Made with ❤️ for better emotional wellness</p>
</div>
""", unsafe_allow_html=True)
