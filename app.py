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

# Simple CSS with dark text on white background
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Lexend+Deca:wght@300;400;500;600;700&display=swap');
    
    .stApp {
        background-color: white;
        font-family: 'Lexend Deca', sans-serif;
    }
    
    .main-title {
        font-size: 2.5rem;
        font-weight: 600;
        text-align: center;
        color: #1a1a1a;
        margin-bottom: 0.5rem;
        font-family: 'Lexend Deca', sans-serif;
    }
    
    .subtitle {
        font-size: 1.2rem;
        text-align: center;
        color: #666;
        margin-bottom: 3rem;
        font-family: 'Lexend Deca', sans-serif;
    }
    
    .decision-card {
        background: #007aff;
        border-radius: 16px;
        padding: 2rem;
        color: white;
        text-align: center;
        margin: 2rem 0;
        box-shadow: 0 4px 20px rgba(0, 122, 255, 0.15);
    }
    
    .recommendation {
        background: #f8f9fa;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        color: #1a1a1a;
        border: 1px solid #dee2e6;
        font-weight: 500;
    }
    
    .do-item {
        background: #d4edda;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        color: #1a1a1a;
        font-weight: 500;
        border-left: 3px solid #28a745;
    }
    
    .dont-item {
        background: #f8d7da;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        color: #1a1a1a;
        font-weight: 500;
        border-left: 3px solid #dc3545;
    }
    
    .weather-card {
        background: #f8f9fa;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        color: #1a1a1a;
        text-align: center;
        border: 1px solid #dee2e6;
    }
    
    .leave-email-card {
        background: #f8f9fa;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        color: #1a1a1a;
        border: 1px solid #dee2e6;
        font-family: 'Courier New', monospace;
        position: relative;
    }
    
    .copy-button {
        background: #28a745;
        color: white;
        border: none;
        border-radius: 6px;
        padding: 0.5rem 1rem;
        font-size: 0.8rem;
        cursor: pointer;
        float: right;
        margin-top: -10px;
    }
    
    .stButton > button {
        width: 100%;
        background: #007aff;
        color: white;
        border: none;
        border-radius: 12px;
        padding: 1rem;
        font-weight: 600;
        font-size: 1rem;
        margin-top: 1.5rem;
        font-family: 'Lexend Deca', sans-serif;
    }
    
    /* Fix for input labels to be black */
    .stSelectbox label,
    .stSlider label,
    .stSelectbox > div > label,
    .stSlider > div > label,
    label[data-testid="stWidgetLabel"] {
        color: #1a1a1a !important;
        font-family: 'Lexend Deca', sans-serif !important;
        font-weight: 500 !important;
    }
    
    /* Additional targeting for labels */
    .stSelectbox > label,
    .stSlider > label {
        color: #1a1a1a !important;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'assessments' not in st.session_state:
    st.session_state.assessments = []
if 'generated_email' not in st.session_state:
    st.session_state.generated_email = ""

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

def generate_leave_email():
    """Generate a believable leave email with variety"""
    import random
    
    # Different excuse categories for variety
    excuses = [
        "food poisoning from last night's dinner",
        "severe stomach flu symptoms",
        "sudden migraine with nausea", 
        "family medical emergency",
        "acute gastroenteritis",
        "high fever and body aches",
        "severe headache and dizziness",
        "sudden illness symptoms",
        "stomach bug that started overnight",
        "urgent family situation"
    ]
    
    excuse = random.choice(excuses)
    
    prompt = f"""Generate a short, professional leave email (2-3 lines) to a line manager using this excuse: {excuse}
    
    Make it sound natural and professionally appropriate. Use this format:
    Subject: [subject line]
    
    Dear [Manager's Name],
    
    [2-3 lines with the excuse and leave request]
    
    Best regards,
    [Your Name]
    
    Vary the wording and tone slightly each time."""
    
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except:
        # Enhanced fallback with more variety
        fallback_templates = [
            f"""Subject: Sick Leave Request - [Your Name]

Dear [Manager's Name],

I'm experiencing {excuse} and won't be able to come to work today. I need to rest and recover to avoid any complications.

Best regards,
[Your Name]""",
            
            f"""Subject: Unable to Attend Work Today

Dear [Manager's Name],

Due to {excuse}, I need to take sick leave today. I apologize for the short notice and will keep you updated on my recovery.

Best regards,
[Your Name]""",
            
            f"""Subject: Sick Leave - [Your Name]

Dear [Manager's Name],

I have {excuse} and need to take the day off to recover properly. I'll be back as soon as I'm feeling better.

Best regards,
[Your Name]"""
        ]
        return random.choice(fallback_templates)

def analyze_leave_decision(data, weather):
    """Enhanced AI analysis for leave recommendation with leave balance consideration"""
    
    # Convert leave balance to numeric factor
    leave_factor = {
        "20+ days left": 0.9,  # High availability
        "15-19 days left": 0.7,  # Good availability  
        "10-14 days left": 0.5,  # Moderate availability
        "5-9 days left": 0.3,  # Low availability
        "0-4 days left": 0.1    # Very limited
    }
    
    leave_multiplier = leave_factor.get(data['leave_taken'], 0.7)
    
    prompt = f"""You are an intelligent work-life balance advisor. Analyze if this person should take leave tomorrow based on their mental state, workload, leave balance, and external factors.

CURRENT STATE:
- Overall feeling: {data['mood']}
- Energy level: {data['energy']}/10
- Sleep quality: {data['sleep']}/10
- Work pressure: {data['work_pressure']}/10
- Personal life stress: {data['personal_stress']}/10
- Physical symptoms: {data['physical_symptoms']}
- Last break taken: {data['last_break']}
- Tomorrow's work importance: {data['tomorrow_importance']}
- Support system: {data['support']}
- Leave remaining this year: {data['leave_taken']}

WEATHER TOMORROW: {weather['temp_high']}°C/{weather['temp_low']}°C, {weather['condition']}, {weather['rain_chance']}% rain chance

LEAVE BALANCE CONSIDERATION:
- If 0-4 days left: Strongly discourage leave unless crisis
- If 5-9 days left: Caution about leave balance, suggest alternatives
- If 10-14 days left: Moderate consideration of leave balance
- If 15+ days left: Leave balance not a major concern

DECISION FRAMEWORK:
- Full Day Leave: For burnout, severe stress, or mental health crisis (consider leave balance)
- Half Day/Early Leave: For moderate stress with manageable work
- Work Normally: For good mental state with support strategies
- Consider weather impact on mood and recovery opportunities
- Factor in leave balance - if high usage, suggest coping strategies instead

Respond in this EXACT JSON format (ensure valid JSON):
{{
    "wellness_score": 45,
    "leave_type": "full_day_leave",
    "confidence": 82,
    "main_reason": "Primary reason for recommendation",
    "decision_summary": "Brief 2-sentence explanation of the decision including leave balance consideration",
    "work_activities": ["3 things to do if working"],
    "work_avoid": ["3 things to avoid if working"],
    "leave_activities": ["4 recovery activities for leave day"],
    "leave_avoid": ["3 things to avoid during leave"],
    "warning_signs": ["signs requiring immediate attention"],
    "recovery_estimate": "Expected recovery timeframe",
    "leave_balance_note": "Comment about leave usage if relevant"
}}

Leave types: "full_day_leave", "half_day_leave", "work_with_care", "work_normally"

SCORING GUIDE (adjusted for leave balance):
- 80-100: Excellent state, work normally
- 60-79: Good state, minor support needed
- 40-59: Moderate stress, consider half day (unless high leave usage)
- 20-39: High stress, likely needs full day (consider leave balance)
- 0-19: Crisis level, definitely needs leave regardless of balance

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
        
        # Enhanced fallback logic with leave balance
        work_pressure_factor = data['work_pressure']
        personal_stress_factor = data['personal_stress']
        energy_factor = data['energy']
        sleep_factor = data['sleep']
        
        # Calculate wellness score
        wellness = 100 - (work_pressure_factor * 6) - (personal_stress_factor * 6) - ((10 - energy_factor) * 8) - ((10 - sleep_factor) * 6)
        wellness = max(5, min(100, int(wellness * leave_multiplier)))  # Adjust for leave balance
        
        # AI-style decision logic based on multiple factors including leave balance
        leave_balance_warning = ""
        ai_justification = ""
        
        if data['leave_taken'] in ["5-9 days left", "0-4 days left"]:
            leave_balance_warning = " Your remaining leave balance is a significant factor in this recommendation."
            ai_justification += f"Considering your limited leave balance ({data['leave_taken']}), "
            if wellness > 30:  # Adjust threshold for low leave remaining
                wellness -= 20  # Penalize for low leave remaining
        
        if wellness < 25:
            leave_type = "full_day_leave"
            ai_justification += f"AI Analysis: Your wellness score is critically low at {wellness}/100. The combination of high work pressure ({work_pressure_factor}/10), personal stress ({personal_stress_factor}/10), and low energy ({energy_factor}/10) indicates severe burnout risk. Immediate rest is essential to prevent long-term health consequences.{leave_balance_warning}"
        elif wellness < 45:
            leave_type = "half_day_leave"  
            ai_justification += f"AI Analysis: Your wellness score is {wellness}/100, indicating moderate stress levels. While you're managing, the elevated work pressure and declining energy suggest you need strategic recovery time. A half day will help reset without depleting your leave balance significantly.{leave_balance_warning}"
        elif wellness < 65:
            leave_type = "work_with_care"
            ai_justification += f"AI Analysis: Your wellness score is {wellness}/100. You can function at work but need careful self-management. The AI detects manageable stress levels but recommends heightened self-care to prevent escalation.{leave_balance_warning}"
        else:
            leave_type = "work_normally"
            ai_justification = f"AI Analysis: Your wellness score is strong at {wellness}/100. The AI assessment shows you're in good psychological and physical condition to work effectively. Your energy levels and stress management are well-balanced."
        
        return {
            "wellness_score": wellness,
            "leave_type": leave_type,
            "confidence": 75,
            "main_reason": f"Work pressure {work_pressure_factor}/10, Energy {energy_factor}/10, Leave left: {data['leave_taken']}",
            "decision_summary": ai_justification,
            "work_activities": ["Take regular breaks every hour", "Prioritize only essential tasks", "Stay hydrated and eat well"],
            "work_avoid": ["Overtime or extra commitments", "Perfectionism on minor tasks", "Skipping lunch break"],
            "leave_activities": ["Sleep until naturally awake", "Light exercise or walk", "Do something you enjoy", "Connect with supportive people"],
            "leave_avoid": ["Checking work emails", "Intensive physical activities", "Making major decisions"],
            "warning_signs": ["Panic attacks", "Complete inability to focus", "Persistent physical symptoms"],
            "recovery_estimate": "1-3 days with proper rest",
            "leave_balance_note": "Consider your remaining leave balance for future plans" if data['leave_taken'] in ["10-14 days left", "5-9 days left", "0-4 days left"] else ""
        }

def main():
    # Header with inline styles to ensure visibility
    st.markdown('<h1 style="font-size: 2.5rem; font-weight: 600; text-align: center; color: #1a1a1a; margin-bottom: 0.5rem; font-family: Lexend Deca, sans-serif;">Should I Take Leave Tomorrow?</h1>', unsafe_allow_html=True)
    st.markdown('<p style="font-size: 1.2rem; text-align: center; color: #666; margin-bottom: 3rem; font-family: Lexend Deca, sans-serif;">AI-powered decision making for your work-life balance</p>', unsafe_allow_html=True)
    
    # Get tomorrow's weather
    weather = get_weather_tomorrow()
    
    # Weather display with inline styles and animation
    # Determine weather icon and animation based on condition
    weather_condition_lower = weather['condition'].lower()
    if 'rain' in weather_condition_lower or 'shower' in weather_condition_lower:
        weather_icon = "🌧️"
        animation_class = "rain-animation"
    elif 'cloud' in weather_condition_lower:
        weather_icon = "☁️"
        animation_class = "cloud-animation"
    elif 'sun' in weather_condition_lower or 'clear' in weather_condition_lower:
        weather_icon = "☀️"
        animation_class = "sun-animation"
    else:
        weather_icon = "🌤️"
        animation_class = "default-animation"
    
    st.markdown(f'''
    <style>
        @keyframes rain-drop {{
            0% {{ transform: translateY(-5px); opacity: 0.7; }}
            50% {{ transform: translateY(2px); opacity: 1; }}
            100% {{ transform: translateY(-5px); opacity: 0.7; }}
        }}
        
        @keyframes cloud-drift {{
            0% {{ transform: translateX(-3px); }}
            50% {{ transform: translateX(3px); }}
            100% {{ transform: translateX(-3px); }}
        }}
        
        @keyframes sun-glow {{
            0% {{ transform: scale(1); opacity: 0.8; }}
            50% {{ transform: scale(1.05); opacity: 1; }}
            100% {{ transform: scale(1); opacity: 0.8; }}
        }}
        
        @keyframes gentle-float {{
            0% {{ transform: translateY(-2px); }}
            50% {{ transform: translateY(2px); }}
            100% {{ transform: translateY(-2px); }}
        }}
        
        .rain-animation {{
            animation: rain-drop 2s ease-in-out infinite;
        }}
        
        .cloud-animation {{
            animation: cloud-drift 4s ease-in-out infinite;
        }}
        
        .sun-animation {{
            animation: sun-glow 3s ease-in-out infinite;
        }}
        
        .default-animation {{
            animation: gentle-float 3s ease-in-out infinite;
        }}
    </style>
    <div style="background: #f8f9fa; border-radius: 12px; padding: 1.5rem; margin: 1rem 0; color: #1a1a1a; text-align: center; border: 1px solid #dee2e6; font-family: Lexend Deca, sans-serif;">
        <h3 style="margin: 0; color: #1a1a1a; font-weight: 600; font-family: Lexend Deca, sans-serif;">Tomorrow's Weather in Dhaka</h3>
        <div style="font-size: 2rem; margin: 0.5rem 0;" class="{animation_class}">{weather_icon}</div>
        <p style="font-size: 1.1rem; margin: 0.5rem 0; color: #1a1a1a; font-family: Lexend Deca, sans-serif;">
            <strong style="color: #1a1a1a; font-family: Lexend Deca, sans-serif;">{weather['temp_high']}°C / {weather['temp_low']}°C</strong><br>
            {weather['condition']} • {weather['rain_chance']}% chance of rain
        </p>
    </div>
    ''', unsafe_allow_html=True)
    
    # Input section header
    st.markdown('<h3 style="color: #1a1a1a; font-family: Lexend Deca, sans-serif; font-weight: 600;">How are you feeling today?</h3>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        mood = st.selectbox(
            "Overall mood",
            ["Excellent", "Good", "Okay", "Struggling", "Overwhelmed", "Exhausted"],
            help="How would you describe your general state today?"
        )
        
        energy = st.slider("Energy level", 1, 10, 5, help="1 = Completely drained, 10 = Highly energized")
        sleep = st.slider("Last night's sleep quality", 1, 10, 6, help="1 = Terrible, 10 = Perfect rest")
        
        leave_taken = st.selectbox(
            "Estimated leave days left",
            ["20+ days left", "15-19 days left", "10-14 days left", "5-9 days left", "0-4 days left"],
            help="How many leave days do you estimate you have remaining this year"
        )
        
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
            'sleep': sleep,
            'work_pressure': work_pressure,
            'personal_stress': personal_stress,
            'physical_symptoms': physical_symptoms,
            'last_break': last_break,
            'tomorrow_importance': tomorrow_importance,
            'support': support,
            'leave_taken': leave_taken
        }
        
        with st.spinner("🤖 Analyzing your situation with AI..."):
            # Force refresh of email generation
            if analysis['leave_type'] in ['full_day_leave', 'half_day_leave']:
                st.session_state.generated_email = generate_leave_email()
            
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
            
            decision_text, decision_color = leave_type_map.get(analysis['leave_type'], ("Work With Care", "#007aff"))
            
            # Decision card with inline styles
            st.markdown(f"""
            <div style="background: #007aff; border-radius: 16px; padding: 2rem; color: white; text-align: center; margin: 2rem 0; box-shadow: 0 4px 20px rgba(0, 122, 255, 0.15); font-family: Lexend Deca, sans-serif;">
                <h2 style="margin: 0; font-weight: 600; color: white; font-family: Lexend Deca, sans-serif;">{decision_text}</h2>
                <p style="font-size: 1.1rem; opacity: 0.9; margin: 1rem 0; color: white; font-family: Lexend Deca, sans-serif;">{analysis['decision_summary']}</p>
                <p style="font-size: 0.9rem; opacity: 0.8; color: white; font-family: Lexend Deca, sans-serif;">Confidence: {analysis['confidence']}%</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Show leave balance note if relevant
            if analysis.get('leave_balance_note'):
                st.markdown(f"""
                <div style="background: #fff3cd; border-radius: 12px; padding: 1rem; margin: 1rem 0; color: #856404; border: 1px solid #ffeaa7; font-weight: 500; font-family: Lexend Deca, sans-serif;">
                    💡 <strong>Leave Balance:</strong> {analysis['leave_balance_note']}
                </div>
                """, unsafe_allow_html=True)
            
            # Display leave email if leave is recommended
            if analysis['leave_type'] in ['full_day_leave', 'half_day_leave'] and st.session_state.generated_email:
                st.markdown('<h3 style="color: #1a1a1a; font-family: Lexend Deca, sans-serif; font-weight: 600;">📧 Leave Email Draft</h3>', unsafe_allow_html=True)
                
                # Email display with copy functionality
                email_container = st.container()
                with email_container:
                    st.markdown(f"""
                    <div style="background: #f8f9fa; border-radius: 12px; padding: 1.5rem; margin: 1rem 0; color: #1a1a1a; border: 1px solid #dee2e6; position: relative; font-family: 'Courier New', monospace;">
                        <pre style="margin: 0; white-space: pre-wrap; color: #1a1a1a; font-family: 'Courier New', monospace;">{st.session_state.generated_email}</pre>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Simple copy button with text selection
                    col1, col2, col3 = st.columns([1, 1, 1])
                    with col2:
                        st.markdown("""
                        <div style="text-align: center; margin: 1rem 0;">
                            <p style="color: #666; font-size: 0.9rem; margin-bottom: 0.5rem; font-family: 'Lexend Deca', sans-serif;">Select the email text above and copy it (Ctrl+C / Cmd+C)</p>
                            <button onclick="selectEmailText()" style="background: #28a745; color: white; border: none; border-radius: 8px; padding: 0.75rem 1.5rem; font-size: 1rem; cursor: pointer; font-family: 'Lexend Deca', sans-serif; font-weight: 600;">
                                📋 Select Email Text
                            </button>
                        </div>
                        
                        <script>
                        function selectEmailText() {
                            // Find the email text element
                            const emailElement = document.querySelector('pre');
                            if (emailElement) {
                                // Create a range and select the text
                                const range = document.createRange();
                                range.selectNodeContents(emailElement);
                                const selection = window.getSelection();
                                selection.removeAllRanges();
                                selection.addRange(range);
                                
                                // Try to copy to clipboard
                                try {
                                    document.execCommand('copy');
                                    alert('Email text selected and copied to clipboard!');
                                } catch (err) {
                                    alert('Email text selected! Please press Ctrl+C (or Cmd+C) to copy.');
                                }
                            }
                        }
                        </script>
                        """, unsafe_allow_html=True)
            
            # Recommendations based on decision
            col1, col2 = st.columns(2)
            
            if analysis['leave_type'] in ['full_day_leave', 'half_day_leave']:
                with col1:
                    st.markdown('<p style="color: #1a1a1a; font-family: Lexend Deca, sans-serif; font-weight: 600;">Recovery Activities:</p>', unsafe_allow_html=True)
                    for item in analysis.get('leave_activities', []):
                        st.markdown(f'<div style="background: #d4edda; border-radius: 8px; padding: 1rem; margin: 0.5rem 0; color: #1a1a1a; font-weight: 500; border-left: 3px solid #28a745; font-family: Lexend Deca, sans-serif;">{item}</div>', unsafe_allow_html=True)
                
                with col2:
                    st.markdown('<p style="color: #1a1a1a; font-family: Lexend Deca, sans-serif; font-weight: 600;">Avoid During Leave:</p>', unsafe_allow_html=True)
                    for item in analysis.get('leave_avoid', []):
                        st.markdown(f'<div style="background: #f8d7da; border-radius: 8px; padding: 1rem; margin: 0.5rem 0; color: #1a1a1a; font-weight: 500; border-left: 3px solid #dc3545; font-family: Lexend Deca, sans-serif;">{item}</div>', unsafe_allow_html=True)
            else:
                with col1:
                    st.markdown('<p style="color: #1a1a1a; font-family: Lexend Deca, sans-serif; font-weight: 600;">If You Work Tomorrow:</p>', unsafe_allow_html=True)
                    for item in analysis.get('work_activities', []):
                        st.markdown(f'<div style="background: #d4edda; border-radius: 8px; padding: 1rem; margin: 0.5rem 0; color: #1a1a1a; font-weight: 500; border-left: 3px solid #28a745; font-family: Lexend Deca, sans-serif;">{item}</div>', unsafe_allow_html=True)
                
                with col2:
                    st.markdown('<p style="color: #1a1a1a; font-family: Lexend Deca, sans-serif; font-weight: 600;">Avoid While Working:</p>', unsafe_allow_html=True)
                    for item in analysis.get('work_avoid', []):
                        st.markdown(f'<div style="background: #f8d7da; border-radius: 8px; padding: 1rem; margin: 0.5rem 0; color: #1a1a1a; font-weight: 500; border-left: 3px solid #dc3545; font-family: Lexend Deca, sans-serif;">{item}</div>', unsafe_allow_html=True)
            
            # Warning signs and recovery time
            if analysis.get('warning_signs'):
                st.markdown(f"""
                <div style="background: #f8f9fa; border-radius: 12px; padding: 1.5rem; margin: 1rem 0; color: #1a1a1a; border: 1px solid #dee2e6; font-weight: 500; font-family: Lexend Deca, sans-serif;">
                    <strong style="color: #1a1a1a; font-family: Lexend Deca, sans-serif;">Watch for these warning signs:</strong><br>
                    {' • '.join(analysis['warning_signs'])}
                </div>
                """, unsafe_allow_html=True)
            
            if analysis.get('recovery_estimate'):
                st.markdown(f"""
                <div style="background: #f8f9fa; border-radius: 12px; padding: 1.5rem; margin: 1rem 0; color: #1a1a1a; border: 1px solid #dee2e6; font-weight: 500; font-family: Lexend Deca, sans-serif;">
                    <strong style="color: #1a1a1a; font-family: Lexend Deca, sans-serif;">Expected recovery time:</strong> {analysis['recovery_estimate']}
                </div>
                """, unsafe_allow_html=True)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; font-size: 0.9rem; padding: 1.5rem; font-family: Lexend Deca, sans-serif;">
        <strong style="color: #666; font-family: Lexend Deca, sans-serif;">Your wellbeing matters.</strong> This tool provides guidance, not medical advice.<br>
        For serious mental health concerns, please consult a healthcare professional.
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
