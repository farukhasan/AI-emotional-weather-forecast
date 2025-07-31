# Should I Take Leave Tomorrow?

An AI-powered Streamlit app that helps you decide whether to take a day off work based on your mental health and stress levels.

## How It Works

The app uses Google Gemini 1.5 Flash to analyze your current wellness state and provide personalized leave recommendations. The AI considers your mood, energy, stress levels, sleep quality, work pressure, and tomorrow's weather to make informed suggestions.

## How to Use

1. Answer the wellness questionnaire about your current state
2. Provide information about work pressure and support system
3. Click "Get My Personalized Recommendation"
4. Receive AI-powered advice with specific activities and warnings

## How the AI Decides

The AI analyzes your responses using a comprehensive wellness framework that weighs multiple factors:

- **Stress vs Energy Balance**: High stress combined with low energy signals need for rest
- **Sleep Quality Impact**: Poor sleep affects decision-making and recovery capacity
- **Work Pressure Assessment**: Evaluates if tomorrow's workload is manageable in your current state
- **Physical Symptoms**: Considers how your body is responding to stress
- **Support System Strength**: Factors in available emotional and practical support
- **Weather Influence**: Accounts for how environmental conditions may affect mood and recovery

The AI prioritizes your mental health by recognizing that taking time off when needed prevents burnout, improves long-term productivity, and maintains overall wellbeing. It understands that pushing through exhaustion or high stress often leads to worse outcomes than taking proactive rest.

## AI Technology

Built with Google Gemini 1.5 Flash model, the AI analyzes wellness patterns and provides structured recommendations with confidence scores. Includes fallback logic for reliability.

Weather data is integrated from Pirate Weather API to factor environmental conditions into decision-making.
