"""
Air Quality Predictor Dashboard

Interactive web dashboard for AQI predictions.

Run:
    streamlit run src/dashboard/app.py

Features:
- City selection
- Current AQI input
- 24-hour forecast
- Interactive charts
- Model comparison
"""

import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import time

# ============================================================================
# PAGE CONFIG
# ============================================================================

st.set_page_config(
    page_title="Air Quality Predictor",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# CONSTANTS
# ============================================================================

API_URL = "http://localhost:8000"

CITIES = {
    "Bangkok": "bangkok",
    "Durban": "durban",
    "São Paulo": "sao_paulo",
    "Sydney": "sydney",
    "London": "london",
    "New York": "new_york"
}

MODELS = {
    "XGBoost (Best)": "xgboost",
    "LightGBM (Fast)": "lightgbm",
    "Random Forest": "random_forest",
    "Linear Regression": "linear_regression"
}

AQI_COLORS = {
    "Good": "#00E400",
    "Moderate": "#FFFF00",
    "Unhealthy for Sensitive Groups": "#FF7E00",
    "Unhealthy": "#FF0000",
    "Very Unhealthy": "#8F3F97",
    "Hazardous": "#7E0023"
}

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def check_api_health():
    """Check if API is running."""
    try:
        response = requests.get(f"{API_URL}/health", timeout=2)
        return response.status_code == 200
    except:
        return False


def get_aqi_color(aqi_value):
    """Get color for AQI value."""
    if aqi_value <= 1.5:
        return "#00E400"  # Green
    elif aqi_value <= 2.5:
        return "#FFFF00"  # Yellow
    elif aqi_value <= 3.5:
        return "#FF7E00"  # Orange
    elif aqi_value <= 4.5:
        return "#FF0000"  # Red
    else:
        return "#8F3F97"  # Purple


def get_aqi_category(aqi_value):
    """Get AQI category name."""
    if aqi_value <= 1.5:
        return "Good"
    elif aqi_value <= 2.5:
        return "Moderate"
    elif aqi_value <= 3.5:
        return "Unhealthy for Sensitive Groups"
    elif aqi_value <= 4.5:
        return "Unhealthy"
    elif aqi_value <= 5.0:
        return "Very Unhealthy"
    else:
        return "Hazardous"


def make_prediction(city, pollutants, model):
    """Call API to make prediction."""
    try:
        response = requests.post(
            f"{API_URL}/predict",
            json={
                "city": city,
                "model": model,
                **pollutants
            },
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API Error: {response.status_code}")
            return None
            
    except Exception as e:
        st.error(f"Connection Error: {str(e)}")
        return None


def create_gauge_chart(current_aqi, predicted_aqi):
    """Create gauge chart for AQI comparison."""
    fig = go.Figure()
    
    # Current AQI gauge
    fig.add_trace(go.Indicator(
        mode="gauge+number+delta",
        value=current_aqi,
        domain={'x': [0, 0.45], 'y': [0, 1]},
        title={'text': "Current AQI", 'font': {'size': 20}},
        delta={'reference': 2.5, 'increasing': {'color': "red"}},
        gauge={
            'axis': {'range': [None, 5], 'tickwidth': 1},
            'bar': {'color': get_aqi_color(current_aqi)},
            'steps': [
                {'range': [0, 1.5], 'color': '#E8F5E9'},
                {'range': [1.5, 2.5], 'color': '#FFF9C4'},
                {'range': [2.5, 3.5], 'color': '#FFE0B2'},
                {'range': [3.5, 4.5], 'color': '#FFCDD2'},
                {'range': [4.5, 5], 'color': '#F3E5F5'}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 3.5
            }
        }
    ))
    
    # Predicted AQI gauge
    fig.add_trace(go.Indicator(
        mode="gauge+number+delta",
        value=predicted_aqi,
        domain={'x': [0.55, 1], 'y': [0, 1]},
        title={'text': "Predicted (24h)", 'font': {'size': 20}},
        delta={'reference': current_aqi, 'increasing': {'color': "red"}},
        gauge={
            'axis': {'range': [None, 5], 'tickwidth': 1},
            'bar': {'color': get_aqi_color(predicted_aqi)},
            'steps': [
                {'range': [0, 1.5], 'color': '#E8F5E9'},
                {'range': [1.5, 2.5], 'color': '#FFF9C4'},
                {'range': [2.5, 3.5], 'color': '#FFE0B2'},
                {'range': [3.5, 4.5], 'color': '#FFCDD2'},
                {'range': [4.5, 5], 'color': '#F3E5F5'}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 3.5
            }
        }
    ))
    
    fig.update_layout(
        height=300,
        margin=dict(l=20, r=20, t=50, b=20)
    )
    
    return fig


def create_forecast_chart(current_aqi, predicted_aqi, confidence_interval):
    """Create 24-hour forecast chart."""
    # Generate hourly progression (simple linear interpolation)
    hours = list(range(25))
    
    # Linear interpolation from current to predicted
    aqi_values = [
        current_aqi + (predicted_aqi - current_aqi) * (h / 24)
        for h in hours
    ]
    
    # Confidence bounds
    upper_bound = [val + (confidence_interval['upper'] - predicted_aqi) 
                  for val in aqi_values]
    lower_bound = [val - (predicted_aqi - confidence_interval['lower']) 
                  for val in aqi_values]
    
    # Create figure
    fig = go.Figure()
    
    # Confidence interval
    fig.add_trace(go.Scatter(
        x=hours + hours[::-1],
        y=upper_bound + lower_bound[::-1],
        fill='toself',
        fillcolor='rgba(0,100,200,0.2)',
        line=dict(color='rgba(255,255,255,0)'),
        name='Confidence Interval',
        showlegend=True
    ))
    
    # AQI forecast line
    fig.add_trace(go.Scatter(
        x=hours,
        y=aqi_values,
        mode='lines+markers',
        name='Predicted AQI',
        line=dict(color='#1f77b4', width=3),
        marker=dict(size=6)
    ))
    
    # Current point
    fig.add_trace(go.Scatter(
        x=[0],
        y=[current_aqi],
        mode='markers',
        name='Current',
        marker=dict(size=15, color='red', symbol='star')
    ))
    
    # 24h prediction point
    fig.add_trace(go.Scatter(
        x=[24],
        y=[predicted_aqi],
        mode='markers',
        name='24h Prediction',
        marker=dict(size=15, color='green', symbol='star')
    ))
    
    # Add AQI level bands
    fig.add_hrect(y0=0, y1=1.5, fillcolor="green", opacity=0.1, 
                  line_width=0, annotation_text="Good", annotation_position="left")
    fig.add_hrect(y0=1.5, y1=2.5, fillcolor="yellow", opacity=0.1, 
                  line_width=0, annotation_text="Moderate", annotation_position="left")
    fig.add_hrect(y0=2.5, y1=3.5, fillcolor="orange", opacity=0.1, 
                  line_width=0, annotation_text="Unhealthy (Sensitive)", annotation_position="left")
    fig.add_hrect(y0=3.5, y1=4.5, fillcolor="red", opacity=0.1, 
                  line_width=0, annotation_text="Unhealthy", annotation_position="left")
    
    fig.update_layout(
        title="24-Hour Air Quality Forecast",
        xaxis_title="Hours from Now",
        yaxis_title="Air Quality Index (AQI)",
        yaxis=dict(range=[0, 5]),
        hovermode='x unified',
        height=400
    )
    
    return fig


# ============================================================================
# MAIN APP
# ============================================================================

def main():
    """Main dashboard application."""
    
    # Header
    st.title("🌍 Air Quality Predictor")
    st.markdown("Predict air quality 24 hours in advance using machine learning")
    
    # Check API health
    if not check_api_health():
        st.error("⚠️ API is not running!")
        st.info("Please start the API first: `uvicorn src.api.main:app --reload`")
        st.stop()
    
    st.success("✅ Connected to API")
    
    # ========================================================================
    # SIDEBAR - User Inputs
    # ========================================================================
    
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # City selection
        city_name = st.selectbox(
            "Select City",
            options=list(CITIES.keys()),
            index=0
        )
        city_code = CITIES[city_name]
        
        st.markdown("---")
        
        # Model selection
        model_name = st.selectbox(
            "Select Model",
            options=list(MODELS.keys()),
            index=0,
            help="XGBoost is recommended for best accuracy"
        )
        model_code = MODELS[model_name]
        
        st.markdown("---")
        
        st.subheader("📊 Current Pollutant Levels")
        
        # Pollutant inputs
        aqi = st.slider("Current AQI", 1.0, 5.0, 2.5, 0.1)
        pm2_5 = st.number_input("PM2.5 (μg/m³)", 0.0, 500.0, 25.0, 1.0)
        pm10 = st.number_input("PM10 (μg/m³)", 0.0, 600.0, 45.0, 1.0)
        no2 = st.number_input("NO2 (μg/m³)", 0.0, 400.0, 15.0, 1.0)
        o3 = st.number_input("O3 (μg/m³)", 0.0, 500.0, 85.0, 1.0)
        
        # Advanced pollutants (collapsed)
        with st.expander("Advanced Pollutants (Optional)"):
            co = st.number_input("CO (μg/m³)", 0.0, 30000.0, 250.0, 10.0)
            so2 = st.number_input("SO2 (μg/m³)", 0.0, 1000.0, 5.0, 1.0)
            nh3 = st.number_input("NH3 (μg/m³)", 0.0, 200.0, 2.0, 0.1)
        
        st.markdown("---")
        
        # Predict button
        predict_button = st.button("🔮 Predict", type="primary", use_container_width=True)
    
    # ========================================================================
    # MAIN AREA - Results
    # ========================================================================
    
    if predict_button:
        with st.spinner(f"Predicting air quality for {city_name}..."):
            
            # Prepare pollutants
            pollutants = {
                "aqi": aqi,
                "pm2_5": pm2_5,
                "pm10": pm10,
                "no2": no2,
                "o3": o3,
                "co": co,
                "so2": so2,
                "nh3": nh3
            }
            
            # Make prediction
            result = make_prediction(city_code, pollutants, model_code)
            
            if result:
                # Store in session state
                st.session_state['last_prediction'] = result
                st.session_state['current_aqi'] = aqi
    
    # Display results if available
    if 'last_prediction' in st.session_state:
        result = st.session_state['last_prediction']
        current_aqi = st.session_state['current_aqi']
        
        # ====================================================================
        # RESULTS DISPLAY
        # ====================================================================
        
        st.markdown("---")
        st.header(f"📍 {result['city']}")
        
        # Key metrics in columns
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Current AQI",
                f"{current_aqi:.2f}",
                help="Current air quality index"
            )
        
        with col2:
            delta = result['predicted_aqi'] - current_aqi
            st.metric(
                "Predicted (24h)",
                f"{result['predicted_aqi']:.2f}",
                f"{delta:+.2f}",
                delta_color="inverse"
            )
        
        with col3:
            st.metric(
                "Category",
                result['predicted_category'],
                help="Air quality category"
            )
        
        with col4:
            confidence_range = result['confidence_interval']['upper'] - result['confidence_interval']['lower']
            st.metric(
                "Confidence",
                f"±{confidence_range/2:.2f}",
                help="Prediction uncertainty"
            )
        
        # Health message
        category = result['predicted_category']
        color = AQI_COLORS.get(category, "#999999")
        
        st.markdown(
            f"""
            <div style="background-color: {color}; padding: 20px; border-radius: 10px; color: black;">
                <h3 style="margin: 0;">💬 Health Recommendation</h3>
                <p style="margin: 10px 0 0 0; font-size: 16px;">{result['health_message']}</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        st.markdown("---")
        
        # Visualizations
        tab1, tab2, tab3 = st.tabs(["📊 Gauges", "📈 Forecast", "ℹ️ Details"])
        
        with tab1:
            st.plotly_chart(
                create_gauge_chart(current_aqi, result['predicted_aqi']),
                use_container_width=True
            )
        
        with tab2:
            st.plotly_chart(
                create_forecast_chart(
                    current_aqi,
                    result['predicted_aqi'],
                    result['confidence_interval']
                ),
                use_container_width=True
            )
        
        with tab3:
            st.subheader("Prediction Details")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Model Information:**")
                st.write(f"- Model: {result['model_used']}")
                st.write(f"- Timestamp: {result['timestamp']}")
                st.write(f"- City: {result['city']}")
            
            with col2:
                st.write("**Confidence Interval:**")
                st.write(f"- Lower bound: {result['confidence_interval']['lower']:.2f}")
                st.write(f"- Predicted: {result['predicted_aqi']:.2f}")
                st.write(f"- Upper bound: {result['confidence_interval']['upper']:.2f}")
    
    else:
        # Welcome message
        st.info("👈 Select a city and enter pollutant levels, then click 'Predict' to see the forecast!")
        
        # Show example
        with st.expander("📖 How to use this dashboard"):
            st.markdown("""
            1. **Select a city** from the sidebar
            2. **Choose a model** (XGBoost recommended)
            3. **Enter current pollutant levels**:
               - AQI: Current air quality index (1-5)
               - PM2.5: Fine particulate matter
               - PM10: Coarse particulate matter
               - NO2: Nitrogen dioxide
               - O3: Ozone
            4. Click **Predict** to get 24-hour forecast
            5. View results with gauges and charts
            
            **AQI Categories:**
            - 🟢 **1.0-1.5**: Good
            - 🟡 **1.5-2.5**: Moderate
            - 🟠 **2.5-3.5**: Unhealthy for Sensitive Groups
            - 🔴 **3.5-4.5**: Unhealthy
            - 🟣 **4.5-5.0**: Very Unhealthy
            """)
    
    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style="text-align: center; color: #666;">
            <p>Air Quality Predictor | Powered by Machine Learning</p>
            <p>Data updates every hour | Predictions valid for 24 hours</p>
        </div>
        """,
        unsafe_allow_html=True
    )


# ============================================================================
# RUN APP
# ============================================================================

if __name__ == "__main__":
    main()