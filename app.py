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
    page_title="🌤️ Emotional Weather Forecast",
    page_icon="🌤️",
    layout="wide"
)

# Initialize session state
if 'mood_history' not in st.session_state:
    st.session_state.mood_history = []

# API Keys (use Streamlit secrets)
try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
    WEATHER_API_KEY = st.secrets.get("PIRATE_WEATHER_API_KEY", "")  # Changed to Pirate Weather
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-pro')
except:
    st.error("⚠️ Please add your API keys to Streamlit secrets!")
    st.stop()

def get_weather_data(lat=23.8103, lon=90.4125):  # Default: Dhaka coordinates
    """Get real weather data using Pirate Weather API (free 20k calls/month)"""
    if not WEATHER_API_KEY:
        # Mock weather data
        return {"condition": "sunny", "temp": 28, "humidity": 75, "description": "Clear skies"}
    
    try:
        # Pirate Weather API endpoint
        url = f"https://api.pirateweather.net/forecast/{WEATHER_API_KEY}/{lat},{lon}"
        response = requests.get(url, timeout=5)
        data = response.json()
        
        current = data["currently"]
        return {
            "condition": current["icon"].replace("-", "_"),  # e.g., "partly-cloudy-day" -> "partly_cloudy_day"
            "temp": round((current["temperature"] - 32) * 5/9),  # Convert F to C
            "humidity": round(current["humidity"] * 100),  # Convert to percentage
            "description": current["summary"],
            "feels_like": round((current["apparentTemperature"] - 32) * 5/9)
        }
    except Exception as e:
        print(f"Weather API error: {e}")
        return {"condition": "sunny", "temp": 28, "humidity": 75, "description": "Clear skies"}

def generate_ai_forecast(mood_data, weather_data, mood_history):
    """Generate AI-powered emotional forecast using Gemini"""
    
    # Prepare context for AI
    history_summary = ""
    if mood_history:
        recent_moods = [entry['mood'] for entry in mood_history[-7:]]
        history_summary = f"Recent mood pattern: {', '.join(recent_moods)}"
    
    prompt = f"""
    You are an emotional wellness AI coach. Analyze this person's current state and provide a personalized emotional forecast.

    Current State:
    - Mood: {mood_data['mood']}
    - Energy Level: {mood_data['energy']}/10
    - Emotional Stability: {mood_data['stability']}/10
    - Sleep Hours: {mood_data['sleep']}
    - Stress Level: {mood_data['stress']}/10
    - Today's Events: {mood_data.get('events', 'None specified')}
    
    Environmental Context:
    - Weather: {weather_data['condition']}, {weather_data['temp']}°C (feels like {weather_data.get('feels_like', weather_data['temp'])}°C)
    - Description: {weather_data.get('description', 'N/A')}
    - Humidity: {weather_data['humidity']}%
    
    {history_summary}

    Provide a response in this JSON format:
    {{
        "forecast_type": "sunny/cloudy/stormy/energetic",
        "confidence": "percentage like 85%",
        "weather_description": "one-line emotional weather description",
        "key_insights": ["insight1", "insight2", "insight3"],
        "recommended_actions": ["action1", "action2", "action3", "action4"],
        "risk_factors": ["risk1", "risk2"],
        "optimal_times": ["time recommendation1", "time recommendation2"],
        "energy_management": "specific energy advice for today"
    }}

    Be specific, actionable, and encouraging. Consider the person's energy and stability levels carefully.
    """
    
    try:
        response = model.generate_content(prompt)
        # Clean the response to extract JSON
        response_text = response.text.strip()
        if response_text.startswith('```json'):
            response_text = response_text[7:-3]
        elif response_text.startswith('```'):
            response_text = response_text[3:-3]
        
        forecast = json.loads(response_text)
        return forecast
    except Exception as e:
        st.error(f"AI Analysis Error: {e}")
        # Fallback forecast
        return {
            "forecast_type": "cloudy",
            "confidence": "75%",
            "weather_description": "Mixed emotional conditions expected",
            "key_insights": ["Analysis temporarily unavailable"],
            "recommended_actions": ["Take regular breaks", "Stay hydrated"],
            "risk_factors": ["Monitor stress levels"],
            "optimal_times": ["Morning hours may be best"],
            "energy_management": "Pace yourself throughout the day"
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
    """Create mood trend visualization"""
    if len(st.session_state.mood_history) < 2:
        return None
    
    df = pd.DataFrame(st.session_state.mood_history)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')
    
    # Calculate overall mood score
    df['mood_score'] = (df['energy'] + df['stability'] + (10 - df['stress'])) / 3
    
    fig = px.line(df, x='date', y='mood_score', 
                  title='Your Emotional Weather Trend',
                  labels={'mood_score': 'Overall Emotional Score', 'date': 'Date'})
    fig.update_layout(height=300)
    return fig

# Main App
def main():
    st.title("🌤️ Emotional Weather Forecast")
    st.markdown("*Predict and prepare for your emotional day ahead*")
    
    # Get current weather
    weather_data = get_weather_data()
    
    # Sidebar for weather info
    with st.sidebar:
        st.header("🌍 Environmental Context")
        st.metric("Weather", weather_data.get('description', weather_data['condition'].title()))
        st.metric("Temperature", f"{weather_data['temp']}°C")
        if 'feels_like' in weather_data:
            st.metric("Feels Like", f"{weather_data['feels_like']}°C")
        st.metric("Humidity", f"{weather_data['humidity']}%")
        
        if st.session_state.mood_history:
            st.header("📊 Quick Stats")
            recent_entry = st.session_state.mood_history[0]
            st.metric("Last Check-in", recent_entry['date'])
            st.metric("Entries This Week", len([e for e in st.session_state.mood_history 
                                             if datetime.fromisoformat(e['timestamp']).date() >= 
                                             (datetime.now() - timedelta(days=7)).date()]))
    
    # Main content in two columns
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.header("📝 Today's Check-in")
        
        # Mood selection
        mood_options = {
            'energetic': '⚡ Energetic',
            'calm': '☁️ Calm', 
            'happy': '☀️ Happy',
            'anxious': '🌧️ Anxious',
            'tired': '🌙 Tired',
            'focused': '☕ Focused'
        }
        
        current_mood = st.selectbox("How are you feeling right now?", 
                                   options=list(mood_options.keys()),
                                   format_func=lambda x: mood_options[x])
        
        # Sliders with better labels
        energy_level = st.slider("Energy Level", 1, 10, 5, 
                                help="1=Completely drained, 10=Highly energized")
        
        stability = st.slider("Emotional Stability", 1, 10, 5,
                             help="1=Very shaky/volatile, 10=Rock solid/steady")
        
        sleep_hours = st.number_input("Hours of sleep last night", 0, 12, 7)
        
        stress_level = st.slider("Current Stress Level", 1, 10, 3,
                                help="1=Very relaxed, 10=Extremely stressed")
        
        events = st.text_area("Today's events/schedule", 
                             placeholder="e.g., Important meeting at 2pm, dinner with friends...")
        
        # Generate forecast button
        if st.button("🔮 Generate Emotional Forecast", type="primary"):
            mood_data = {
                'mood': current_mood,
                'energy': energy_level,
                'stability': stability,
                'sleep': sleep_hours,
                'stress': stress_level,
                'events': events
            }
            
            with st.spinner("Analyzing your emotional patterns..."):
                forecast = generate_ai_forecast(mood_data, weather_data, st.session_state.mood_history)
                save_mood_entry(mood_data)
                st.session_state.current_forecast = forecast
    
    with col2:
        st.header("🌤️ Your Emotional Forecast")
        
        if 'current_forecast' in st.session_state:
            forecast = st.session_state.current_forecast
            
            # Weather icon mapping
            weather_icons = {
                'sunny': '☀️',
                'cloudy': '☁️', 
                'stormy': '🌧️',
                'energetic': '⚡'
            }
            
            icon = weather_icons.get(forecast['forecast_type'], '🌤️')
            
            # Forecast display
            st.markdown(f"""
            <div style="text-align: center; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 15px; color: white; margin: 10px 0;">
                <h1 style="font-size: 3em; margin: 0;">{icon}</h1>
                <h2 style="margin: 10px 0;">{forecast['weather_description']}</h2>
                <p>Confidence: {forecast['confidence']}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Key insights
            st.subheader("🔍 Key Insights")
            for insight in forecast['key_insights']:
                st.info(f"💡 {insight}")
            
            # Recommended actions
            st.subheader("✅ Recommended Actions")
            for action in forecast['recommended_actions']:
                st.success(f"• {action}")
            
            # Risk factors
            if forecast['risk_factors']:
                st.subheader("⚠️ Watch Out For")
                for risk in forecast['risk_factors']:
                    st.warning(f"• {risk}")
            
            # Optimal times
            st.subheader("⏰ Optimal Timing")
            for time_rec in forecast['optimal_times']:
                st.info(f"🕐 {time_rec}")
            
            # Energy management
            st.subheader("⚡ Energy Management")
            st.markdown(f"**{forecast['energy_management']}**")
        
        else:
            st.info("Complete your check-in to see your personalized emotional forecast!")
    
    # Mood trend chart
    if st.session_state.mood_history:
        st.header("📈 Your Emotional Weather Trend")
        chart = create_mood_trend_chart()
        if chart:
            st.plotly_chart(chart, use_container_width=True)
        
        # Recent history
        with st.expander("📋 Recent Check-ins"):
            df = pd.DataFrame(st.session_state.mood_history[:7])
            if not df.empty:
                display_df = df[['date', 'mood', 'energy', 'stability', 'stress', 'sleep']].copy()
                display_df.columns = ['Date', 'Mood', 'Energy', 'Stability', 'Stress', 'Sleep']
                st.dataframe(display_df, use_container_width=True)

if __name__ == "__main__":
    main()

# Footer
st.markdown("---")
st.markdown("*🌟 Remember: This is a wellness tool, not medical advice. For serious mental health concerns, please consult professionals.*")