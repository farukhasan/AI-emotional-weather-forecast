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
    page_title="Mental Health Day Advisor",
    page_icon="🧠",
    layout="centered"
)

# Minimal, clean CSS
st.markdown("""
<style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 300;
        text-align: center;
        color: #1a1a1a;
        margin-bottom: 0.5rem;
        font-family: -apple-system, BlinkMacSystemFont, sans-serif;
    }
    .subtitle {
        font-size: 1rem;
        text-align: center;
        color: #666;
        margin-bottom: 2rem;
        font-family: -apple-system, BlinkMacSystemFont, sans-serif;
    }
    .decision-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 16px;
        padding: 2rem;
        color: white;
        text-align: center;
        margin: 2rem 0;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
    }
    .wellness-score {
        font-size: 3rem;
        font-weight: 200;
        margin: 1rem 0;
    }
    .recommendation {
        background: #f8f9fa;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        border-left: 4px solid #007aff;
    }
    .do-item {
        background: #e8f5e8;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        border-left: 3px solid #34c759;
    }
    .dont-item {
        background: #fff3cd;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        border-left: 3px solid #ff9500;
    }
    .stButton > button {
        width: 100%;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.8rem;
        font-weight: 500;
        font-size: 1rem;
        margin-top: 1.5rem;
    }
    .input-section {
        background: #fafafa;
        border-radius: 16px;
        padding: 2rem;
        margin: 1rem 0;
    }
    .metric-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin: 0.5rem 0;
        padding: 0.5rem;
        background: white;
        border-radius: 8px;
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

def analyze_mental_health_day_need(data, weather):
    """AI analysis for mental health day recommendation"""
    
    prompt = f"""You are a mental health AI advisor. Based on this person's current state, determine if they should take a mental health day tomorrow.

CURRENT STATE:
- Overall feeling: {data['mood']}
- Energy level: {data['energy']}/10
- Stress level: {data['stress']}/10
- Sleep quality: {data['sleep']}/10
- Work pressure: {data['work_pressure']}/10
- Personal life stress: {data['personal_stress']}/10
- Physical symptoms: {data['physical_symptoms']}
- Last mental health day: {data['last_break']}
- Tomorrow's importance: {data['tomorrow_importance']}
- Support system: {data['support']}

TOMORROW'S WEATHER: {weather['temp_high']}°C/{weather['temp_low']}°C, {weather['condition']}, {weather['rain_chance']}% rain

ANALYSIS REQUIRED:
1. Calculate wellness score (1-100)
2. Determine if mental health day is needed
3. Provide specific reasoning
4. Give actionable recommendations

Respond with this EXACT JSON:
{{
    "wellness_score": number 1-100,
    "take_leave": true or false,
    "confidence": "percentage like 85%",
    "main_reason": "primary reason for the recommendation",
    "decision_summary": "2-sentence explanation",
    "if_working_do": ["3 specific things to do if going to work"],
    "if_working_avoid": ["3 things to avoid if working"],
    "if_on_leave_do": ["4 specific recovery activities for mental health day"],
    "if_on_leave_avoid": ["3 things to avoid during mental health day"],
    "urgent_signs": ["warning signs that require immediate attention"],
    "recovery_timeline": "how long recovery might take"
}}

Consider: High stress (>7) + Low energy (<4) + Poor sleep (<5) + Recent high work pressure = likely needs break
Weather impact: Rainy/gloomy weather may worsen mood, good weather provides recovery opportunities
Support system strength affects recovery ability"""

    try:
        response = model.generate_content(prompt)
        result = json.loads(response.text.strip())
        return result
    except Exception as e:
        # Smart fallback logic
        stress_score = data['stress']
        energy_score = data['energy'] 
        sleep_score = data['sleep']
        work_pressure = data['work_pressure']
        
        # Calculate wellness score
        wellness = 100 - (stress_score * 8) - ((10 - energy_score) * 6) - ((10 - sleep_score) * 5) - (work_pressure * 6)
        wellness = max(10, min(100, wellness))
        
        # Decision logic
        high_stress = stress_score >= 7
        low_energy = energy_score <= 4
        poor_sleep = sleep_score <= 4
        high_work_pressure = work_pressure >= 7
        
        need_break = sum([high_stress, low_energy, poor_sleep, high_work_pressure]) >= 2
        
        if need_break:
            return {
                "wellness_score": wellness,
                "take_leave": True,
                "confidence": "78%",
                "main_reason": "Multiple stress indicators suggest you need recovery time",
                "decision_summary": "Your combination of high stress, low energy, or poor sleep indicates burnout risk. A mental health day will help you reset and return stronger.",
                "if_working_do": ["Take frequent 10-minute breaks", "Delegate non-urgent tasks", "Leave work at normal time"],
                "if_working_avoid": ["Taking on new commitments", "Working through lunch", "Staying late"],
                "if_on_leave_do": ["Sleep in naturally", "Do gentle exercise like walking", "Connect with supportive people", "Do something creative or fun"],
                "if_on_leave_avoid": ["Thinking about work tasks", "Overwhelming social commitments", "Heavy physical activities"],
                "urgent_signs": ["Persistent anxiety or panic", "Complete inability to focus", "Physical symptoms worsening"],
                "recovery_timeline": "1-2 days of good rest should help significantly"
            }
        else:
            return {
                "wellness_score": wellness,
                "take_leave": False,
                "confidence": "72%",
                "main_reason": "You're managing well enough to continue with support strategies",
                "decision_summary": "While you're experiencing some stress, you have enough resilience to work tomorrow. Focus on stress management and recovery activities.",
                "if_working_do": ["Start with easiest tasks first", "Take lunch break away from desk", "Practice 3 deep breaths before meetings"],
                "if_working_avoid": ["Perfectionism on minor tasks", "Skipping breaks", "Negative self-talk"],
                "if_on_leave_do": ["Light exercise or stretching", "Organize something small", "Plan enjoyable evening", "Prepare well for next day"],
                "if_on_leave_avoid": ["Intense planning or thinking", "Comparing yourself to others", "Overcommitting for next week"],
                "urgent_signs": ["Sudden mood changes", "Panic attacks", "Complete exhaustion"],
                "recovery_timeline": "With good self-care, you should feel better in 2-3 days"
            }

def create_wellness_trend():
    """Simple wellness trend chart"""
    if len(st.session_state.assessments) < 2:
        return None
    
    df = pd.DataFrame(st.session_state.assessments[-14:])  # Last 2 weeks
    df['date'] = pd.to_datetime(df['date'])
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['wellness_score'],
        mode='lines+markers',
        line=dict(color='#667eea', width=3),
        marker=dict(size=8, color='#764ba2'),
        fill='tonexty',
        fillcolor='rgba(102, 126, 234, 0.1)'
    ))
    
    fig.update_layout(
        title="Your Wellness Trend",
        xaxis_title="Date",
        yaxis_title="Wellness Score",
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(family="-apple-system, BlinkMacSystemFont, sans-serif"),
        showlegend=False,
        height=300,
        yaxis=dict(range=[0, 100])
    )
    
    return fig

def main():
    # Header
    st.markdown('<h1 class="main-title">Mental Health Day Advisor</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Should you take tomorrow off? Let AI help you decide.</p>', unsafe_allow_html=True)
    
    # Get tomorrow's weather
    weather = get_weather_tomorrow()
    
    # Weather preview
    st.info(f"🌤️ **Tomorrow's Weather:** {weather['temp_high']}°C/{weather['temp_low']}°C, {weather['condition']} ({weather['rain_chance']}% rain)")
    
    # Input section
    st.markdown('<div class="input-section">', unsafe_allow_html=True)
    st.markdown("### Quick Assessment")
    
    col1, col2 = st.columns(2)
    
    with col1:
        mood = st.selectbox(
            "Overall feeling today",
            ["Excellent", "Good", "Okay", "Struggling", "Overwhelmed", "Burned out"],
            help="How would you describe your general state?"
        )
        
        energy = st.slider("Energy level", 1, 10, 5, help="1=Completely drained, 10=Highly energized")
        stress = st.slider("Stress level", 1, 10, 5, help="1=Very calm, 10=Extremely stressed")
        sleep = st.slider("Sleep quality", 1, 10, 6, help="1=Terrible sleep, 10=Perfect rest")
        
    with col2:
        work_pressure = st.slider("Work pressure", 1, 10, 5, help="1=Very light workload, 10=Overwhelming")
        personal_stress = st.slider("Personal life stress", 1, 10, 4, help="1=Very peaceful, 10=Major issues")
        
        physical_symptoms = st.selectbox(
            "Physical symptoms",
            ["None", "Mild (slight headache/tension)", "Moderate (noticeable discomfort)", "Severe (affecting daily activities)"]
        )
        
        last_break = st.selectbox(
            "Last mental health day",
            ["Never taken one", "More than 6 months ago", "2-6 months ago", "1-2 months ago", "Within last month"]
        )
    
    tomorrow_importance = st.selectbox(
        "How important are tomorrow's work commitments?",
        ["Low - mostly routine tasks", "Medium - some important items", "High - critical deadlines", "Extremely high - can't be rescheduled"]
    )
    
    support = st.selectbox(
        "Support system strength",
        ["Strong - family/friends very supportive", "Good - some people I can talk to", "Limited - few supportive people", "Weak - feel quite alone"]
    )
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Analysis button
    if st.button("🧠 Analyze My Mental Health Needs", type="primary"):
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
        
        with st.spinner("🤖 Analyzing your mental health needs..."):
            time.sleep(2)  # Brief pause for UX
            analysis = analyze_mental_health_day_need(data, weather)
            
            # Save assessment
            entry = {
                **data,
                'date': datetime.now().strftime('%Y-%m-%d'),
                'wellness_score': analysis['wellness_score'],
                'recommendation': analysis['take_leave']
            }
            st.session_state.assessments.insert(0, entry)
            st.session_state.assessments = st.session_state.assessments[:30]
            
            # Display results
            decision_color = "#34c759" if not analysis['take_leave'] else "#ff9500"
            decision_text = "Continue Working Tomorrow" if not analysis['take_leave'] else "Take a Mental Health Day"
            
            st.markdown(f"""
            <div class="decision-card" style="background: linear-gradient(135deg, {decision_color}aa 0%, {decision_color}dd 100%);">
                <h2 style="margin: 0; font-weight: 300;">Recommendation</h2>
                <div class="wellness-score">{analysis['wellness_score']}/100</div>
                <h3 style="margin: 0.5rem 0; font-weight: 400;">{decision_text}</h3>
                <p style="font-size: 1rem; opacity: 0.9; margin: 1rem 0;">{analysis['decision_summary']}</p>
                <p style="font-size: 0.9rem; opacity: 0.8;">Confidence: {analysis['confidence']}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Recommendations
            col1, col2 = st.columns(2)
            
            if analysis['take_leave']:
                with col1:
                    st.markdown("**✅ If You Take the Day Off:**")
                    for item in analysis['if_on_leave_do']:
                        st.markdown(f'<div class="do-item">• {item}</div>', unsafe_allow_html=True)
                
                with col2:
                    st.markdown("**⚠️ Avoid During Your Mental Health Day:**")
                    for item in analysis['if_on_leave_avoid']:
                        st.markdown(f'<div class="dont-item">• {item}</div>', unsafe_allow_html=True)
            else:
                with col1:
                    st.markdown("**✅ If You Work Tomorrow:**")
                    for item in analysis['if_working_do']:
                        st.markdown(f'<div class="do-item">• {item}</div>', unsafe_allow_html=True)
                
                with col2:
                    st.markdown("**⚠️ Avoid While Working:**")
                    for item in analysis['if_working_avoid']:
                        st.markdown(f'<div class="dont-item">• {item}</div>', unsafe_allow_html=True)
            
            # Important info
            st.markdown(f"""
            <div class="recommendation">
                <strong>🚨 Watch for these signs:</strong><br>
                {', '.join(analysis['urgent_signs'])}
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div class="recommendation">
                <strong>⏰ Recovery timeline:</strong> {analysis['recovery_timeline']}
            </div>
            """, unsafe_allow_html=True)
    
    # Trend chart
    if len(st.session_state.assessments) >= 2:
        st.markdown("### Your Wellness Journey")
        chart = create_wellness_trend()
        if chart:
            st.plotly_chart(chart, use_container_width=True)
        
        # Quick insights
        recent_scores = [a['wellness_score'] for a in st.session_state.assessments[:7]]
        avg_score = sum(recent_scores) / len(recent_scores)
        
        if avg_score >= 70:
            trend_msg = "📈 Great wellness trend - keep it up!"
        elif avg_score >= 50:
            trend_msg = "📊 Steady wellness - consider more self-care"
        else:
            trend_msg = "📉 Concerning trend - prioritize your mental health"
        
        st.info(f"**7-Day Average Wellness:** {avg_score:.0f}/100 - {trend_msg}")

if __name__ == "__main__":
    main()

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; font-size: 0.85rem; padding: 1rem;">
    💙 Your mental health matters. This tool provides guidance, not medical advice.<br>
    For serious concerns, please consult a mental health professional.
</div>
""", unsafe_allow_html=True)
