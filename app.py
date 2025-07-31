import streamlit as st
import google.generativeai as genai
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
from datetime import datetime, timedelta
import json
import time

# Page config with Apple-like styling
st.set_page_config(
    page_title="MoodCast",
    page_icon="🌤️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for Apple-like minimalist design
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 300;
        text-align: center;
        color: #1d1d1f;
        margin-bottom: 0.5rem;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }
    .sub-header {
        font-size: 1.1rem;
        font-weight: 400;
        text-align: center;
        color: #86868b;
        margin-bottom: 3rem;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }
    .metric-card {
        background: #f5f5f7;
        border-radius: 18px;
        padding: 1.5rem;
        margin: 0.5rem 0;
        border: none;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
    }
    .insight-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 20px;
        padding: 2rem;
        color: white;
        margin: 1rem 0;
        box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3);
    }
    .suggestion-positive {
        background: #e8f5e8;
        border-left: 4px solid #34c759;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 8px;
        font-size: 0.95rem;
    }
    .suggestion-warning {
        background: #fff3cd;
        border-left: 4px solid #ff9500;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 8px;
        font-size: 0.95rem;
    }
    .suggestion-info {
        background: #e8f4f8;
        border-left: 4px solid #007aff;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 8px;
        font-size: 0.95rem;
    }
    .stButton > button {
        width: 100%;
        background: #007aff;
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.75rem;
        font-weight: 500;
        font-size: 1rem;
        margin-top: 1rem;
    }
    .stSelectbox > div > div {
        border-radius: 12px;
        border: 1px solid #d2d2d7;
    }
    .weather-widget {
        background: linear-gradient(135deg, #74b9ff 0%, #0984e3 100%);
        border-radius: 20px;
        padding: 1.5rem;
        color: white;
        text-align: center;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'mood_history' not in st.session_state:
    st.session_state.mood_history = []
if 'current_forecast' not in st.session_state:
    st.session_state.current_forecast = None

# API Configuration
try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
    WEATHER_API_KEY = st.secrets.get("PIRATE_WEATHER_API_KEY", "")
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')  # Free version
except:
    st.error("🔑 Please add your GEMINI_API_KEY to Streamlit secrets")
    st.stop()

def get_weather_data():
    """Get weather data with fallback"""
    try:
        if WEATHER_API_KEY:
            # Simplified weather call
            url = f"https://api.pirateweather.net/forecast/{WEATHER_API_KEY}/23.8103,90.4125"
            response = requests.get(url, timeout=3)
            data = response.json()
            current = data["currently"]
            return {
                "temp": round((current["temperature"] - 32) * 5/9),
                "condition": current.get("summary", "Clear"),
                "humidity": round(current["humidity"] * 100),
                "icon": current.get("icon", "clear-day")
            }
    except:
        pass
    
    # Fallback weather
    return {
        "temp": 28,
        "condition": "Pleasant weather",
        "humidity": 65,
        "icon": "partly-cloudy-day"
    }

def generate_meaningful_forecast(mood_data, weather_data):
    """Generate meaningful, actionable insights using Gemini Flash"""
    
    prompt = f"""You are a compassionate AI wellness coach. Analyze this person's state and provide specific, actionable insights.

CURRENT STATE:
- Feeling: {mood_data['mood']}
- Energy: {mood_data['energy']}/10
- Stress: {mood_data['stress']}/10
- Sleep: {mood_data['sleep']} hours
- Main concern: {mood_data.get('concern', 'None')}
- Today's focus: {mood_data.get('focus', 'General day')}

WEATHER: {weather_data['temp']}°C, {weather_data['condition']}

Respond with this EXACT JSON structure:
{{
    "overall_score": number from 1-10,
    "energy_forecast": "one clear sentence about energy levels",
    "key_insight": "one meaningful observation about their current state",
    "do_this": ["3 specific actions they should take today"],
    "avoid_this": ["2 things they should avoid today"],
    "best_time": "when they should do their most important task",
    "self_care": "one specific self-care suggestion",
    "tomorrow_prep": "one thing to prepare for tomorrow"
}}

Be specific, practical, and kind. Focus on actionable advice, not generic statements."""

    try:
        response = model.generate_content(prompt)
        result = json.loads(response.text.strip())
        return result
    except Exception as e:
        # Meaningful fallback based on inputs
        energy_level = mood_data['energy']
        stress_level = mood_data['stress']
        
        if energy_level >= 7 and stress_level <= 4:
            forecast_type = "high_energy_low_stress"
        elif energy_level <= 4 and stress_level >= 7:
            forecast_type = "low_energy_high_stress" 
        elif energy_level >= 6:
            forecast_type = "good_energy"
        else:
            forecast_type = "low_energy"
        
        fallback_forecasts = {
            "high_energy_low_stress": {
                "overall_score": 8,
                "energy_forecast": "You have great energy and low stress - perfect for tackling important tasks.",
                "key_insight": "This is your optimal state for productivity and decision-making.",
                "do_this": ["Start your most challenging task first", "Have important conversations", "Plan future projects"],
                "avoid_this": ["Wasting time on trivial tasks", "Overthinking decisions"],
                "best_time": "First 3 hours of your day",
                "self_care": "Take a 10-minute walk outside to maintain this positive state",
                "tomorrow_prep": "Plan 3 specific goals for tomorrow while your mind is clear"
            },
            "low_energy_high_stress": {
                "overall_score": 3,
                "energy_forecast": "Your energy is low and stress is high - focus on recovery today.",
                "key_insight": "Your body and mind are signaling the need for rest and gentle care.",
                "do_this": ["Do only essential tasks", "Practice deep breathing for 5 minutes", "Get some sunlight"],
                "avoid_this": ["Making important decisions", "Overwhelming yourself with tasks"],
                "best_time": "After a 20-minute rest or nap",
                "self_care": "Take a warm shower or bath to reset your nervous system",
                "tomorrow_prep": "Prepare everything you need tonight so tomorrow morning is easier"
            },
            "good_energy": {
                "overall_score": 6,
                "energy_forecast": "You have decent energy - use it wisely on meaningful tasks.",
                "key_insight": "You're in a steady state that's good for consistent progress.",
                "do_this": ["Focus on one important task", "Connect with someone you care about", "Move your body"],
                "avoid_this": ["Multitasking too much", "Skipping meals"],
                "best_time": "Mid-morning when your energy peaks",
                "self_care": "Listen to music that makes you feel good",
                "tomorrow_prep": "Set out clothes and prepare breakfast to save morning energy"
            },
            "low_energy": {
                "overall_score": 4,
                "energy_forecast": "Your energy is low - be gentle with yourself today.",
                "key_insight": "Low energy is your body's way of asking for rest and restoration.",
                "do_this": ["Do light, easy tasks", "Hydrate well", "Rest when you need to"],
                "avoid_this": ["Pushing through fatigue", "Comparing yourself to others"],
                "best_time": "Whenever you feel a small surge of motivation",
                "self_care": "Take a 15-minute nap or meditation break",
                "tomorrow_prep": "Go to bed 30 minutes earlier tonight"
            }
        }
        
        return fallback_forecasts.get(forecast_type, fallback_forecasts["good_energy"])

def create_mood_visualization(history):
    """Create a beautiful mood trend chart"""
    if len(history) < 2:
        return None
    
    df = pd.DataFrame(history[:14])  # Last 2 weeks
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')
    
    # Calculate wellness score
    df['wellness_score'] = (df['energy'] + (10 - df['stress'])) / 2
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df['date'], 
        y=df['wellness_score'],
        mode='lines+markers',
        line=dict(color='#007AFF', width=3),
        marker=dict(size=8),
        name='Wellness Score'
    ))
    
    fig.update_layout(
        title="Your Wellness Trend",
        xaxis_title="Date",
        yaxis_title="Wellness Score (1-10)",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family="SF Pro Display, -apple-system, sans-serif"),
        showlegend=False,
        height=300
    )
    
    return fig

def main():
    # Header
    st.markdown('<h1 class="main-header">MoodCast</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Your daily emotional wellness companion</p>', unsafe_allow_html=True)
    
    # Get weather
    weather_data = get_weather_data()
    
    # Weather widget
    weather_icons = {
        "clear-day": "☀️", "clear-night": "🌙", "partly-cloudy-day": "⛅", 
        "partly-cloudy-night": "☁️", "cloudy": "☁️", "rain": "🌧️"
    }
    icon = weather_icons.get(weather_data['icon'], "🌤️")
    
    st.markdown(f"""
    <div class="weather-widget">
        <h3>{icon} {weather_data['temp']}°C</h3>
        <p>{weather_data['condition']}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Main input section
    st.markdown("### How are you feeling today?")
    
    # Simplified, user-friendly inputs
    col1, col2 = st.columns(2)
    
    with col1:
        mood_options = {
            'great': '😊 Great - feeling positive',
            'good': '🙂 Good - pretty solid', 
            'okay': '😐 Okay - just average',
            'stressed': '😰 Stressed - overwhelmed',
            'tired': '😴 Tired - low energy',
            'anxious': '😟 Anxious - worried'
        }
        
        current_mood = st.selectbox(
            "Overall mood",
            options=list(mood_options.keys()),
            format_func=lambda x: mood_options[x],
            help="How would you describe your general feeling right now?"
        )
        
        energy_level = st.select_slider(
            "Energy level",
            options=[1,2,3,4,5,6,7,8,9,10],
            value=5,
            format_func=lambda x: f"{x}/10 {'🔋' * min(int(x/2), 5)}",
            help="How much energy do you have today?"
        )
        
        sleep_hours = st.select_slider(
            "Sleep last night",
            options=[3,4,5,6,7,8,9,10,11,12],
            value=7,
            format_func=lambda x: f"{x} hours",
            help="How many hours did you sleep?"
        )
    
    with col2:
        stress_level = st.select_slider(
            "Stress level", 
            options=[1,2,3,4,5,6,7,8,9,10],
            value=4,
            format_func=lambda x: f"{x}/10 {'😤' * min(int(x/2), 5)}",
            help="How stressed are you feeling?"
        )
        
        main_concern = st.text_input(
            "What's on your mind?",
            placeholder="e.g., big presentation, relationship issue, deadline...",
            help="What's your main concern or focus today?"
        )
        
        focus_area = st.selectbox(
            "Today's main focus",
            ["Work/Study", "Personal relationships", "Health & wellness", "Creative projects", "Rest & recovery", "Social activities"],
            help="What do you want to focus on today?"
        )
    
    # Generate forecast
    if st.button("✨ Get My Daily Insights", type="primary"):
        mood_data = {
            'mood': current_mood,
            'energy': energy_level,
            'stress': stress_level,
            'sleep': sleep_hours,
            'concern': main_concern,
            'focus': focus_area
        }
        
        with st.spinner("🧠 Analyzing your patterns..."):
            time.sleep(1)  # Brief pause for better UX
            forecast = generate_meaningful_forecast(mood_data, weather_data)
            
            # Save entry
            entry = {
                **mood_data,
                'date': datetime.now().strftime('%Y-%m-%d'),
                'timestamp': datetime.now().isoformat(),
                'overall_score': forecast['overall_score']
            }
            st.session_state.mood_history.insert(0, entry)
            st.session_state.mood_history = st.session_state.mood_history[:30]
            st.session_state.current_forecast = forecast
    
    # Display results
    if st.session_state.current_forecast:
        forecast = st.session_state.current_forecast
        
        # Overall insight card
        st.markdown(f"""
        <div class="insight-card">
            <h2 style="margin: 0 0 1rem 0;">Today's Insight</h2>
            <h3 style="margin: 0 0 0.5rem 0; font-weight: 300;">Wellness Score: {forecast['overall_score']}/10</h3>
            <p style="font-size: 1.1rem; margin: 0; opacity: 0.9;">{forecast['key_insight']}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Energy forecast
        st.markdown(f"""
        <div class="suggestion-info">
            <strong>⚡ Energy Forecast:</strong><br>
            {forecast['energy_forecast']}
        </div>
        """, unsafe_allow_html=True)
        
        # Action items
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**✅ Do This Today:**")
            for item in forecast['do_this']:
                st.markdown(f"""
                <div class="suggestion-positive">
                    • {item}
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div class="suggestion-info">
                <strong>🎯 Best Time for Important Tasks:</strong><br>
                {forecast['best_time']}
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("**⚠️ Avoid Today:**")
            for item in forecast['avoid_this']:
                st.markdown(f"""
                <div class="suggestion-warning">
                    • {item}
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div class="suggestion-positive">
                <strong>🌱 Self-Care:</strong><br>
                {forecast['self_care']}
            </div>
            """, unsafe_allow_html=True)
        
        # Tomorrow prep
        st.markdown(f"""
        <div class="suggestion-info">
            <strong>🌅 Prepare for Tomorrow:</strong><br>
            {forecast['tomorrow_prep']}
        </div>
        """, unsafe_allow_html=True)
    
    # Trend visualization
    if len(st.session_state.mood_history) >= 2:
        st.markdown("### Your Wellness Trend")
        chart = create_mood_visualization(st.session_state.mood_history)
        if chart:
            st.plotly_chart(chart, use_container_width=True)
        
        # Quick stats
        recent_scores = [entry['overall_score'] for entry in st.session_state.mood_history[:7]]
        avg_score = sum(recent_scores) / len(recent_scores) if recent_scores else 5
        
        if avg_score >= 7:
            trend_msg = "📈 You're doing great this week!"
        elif avg_score >= 5:
            trend_msg = "📊 You're maintaining steady wellness"
        else:
            trend_msg = "📉 Consider focusing more on self-care"
        
        st.info(f"**7-Day Average:** {avg_score:.1f}/10 - {trend_msg}")

if __name__ == "__main__":
    main()

# Clean footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #86868b; font-size: 0.9rem; padding: 2rem;">
    Made with care for your daily wellness journey
</div>
""", unsafe_allow_html=True)
