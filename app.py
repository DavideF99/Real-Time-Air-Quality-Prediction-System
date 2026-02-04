import gradio as gr
import pandas as pd
import numpy as np
from src.api.predictor import ModelPredictor
from src.data.collectors import AirQualityCollector
from pathlib import Path
import os

# Initialize predictor and data collector
predictor = ModelPredictor()
collector = AirQualityCollector()

def get_aqi_color_and_emoji(prediction):
    """Get color, emoji, and health message based on AQI value."""
    if prediction <= 1:
        return "#10b981", "🟢", "Good", "Air quality is satisfactory, and air pollution poses little or no risk."
    elif prediction <= 2:
        return "#f59e0b", "🟡", "Moderate", "Air quality is acceptable. However, there may be a risk for some people, particularly those who are unusually sensitive to air pollution."
    elif prediction <= 3:
        return "#f97316", "🟠", "Unhealthy for Sensitive Groups", "Members of sensitive groups may experience health effects. The general public is less likely to be affected."
    elif prediction <= 4:
        return "#ef4444", "🔴", "Unhealthy", "Some members of the general public may experience health effects; members of sensitive groups may experience more serious health effects."
    else:
        return "#9333ea", "🟣", "Very Unhealthy / Hazardous", "Health alert: The risk of health effects is increased for everyone."

def fetch_realtime_data(city, model_name):
    """
    Fetch real-time air quality data and make prediction.
    """
    try:
        # Convert city name to city_key format
        city_key = city.lower().replace(' ', '_')
        
        # Fetch real-time data from API
        data = collector.fetch_city_data(city_key)
        
        if not data:
            return create_error_display("Failed to fetch real-time data. Please check your API key or try manual input.")
        
        # Extract pollutant values
        pollutants = {
            'pm2_5': data.get('pm2_5', 0),
            'pm10': data.get('pm10', 0),
            'no2': data.get('no2', 0),
            'o3': data.get('o3', 0),
            'co': data.get('co', 0),
            'so2': data.get('so2', 0),
            'nh3': data.get('nh3', 0)
        }
        
        # Make prediction
        prediction, confidence = predictor.predict(
            city=city_key,
            pollutants=pollutants,
            model_name=model_name
        )
        
        # Create display
        return create_prediction_display(prediction, confidence, pollutants, is_realtime=True)
        
    except Exception as e:
        return create_error_display(f"Error: {str(e)}")

def predict_aqi_manual(city, pm2_5, pm10, no2, o3, co, so2, nh3, model_name):
    """
    Predict AQI based on manually input pollutants.
    """
    pollutants = {
        'pm2_5': pm2_5,
        'pm10': pm10,
        'no2': no2,
        'o3': o3,
        'co': co,
        'so2': so2,
        'nh3': nh3
    }
    
    try:
        prediction, confidence = predictor.predict(
            city=city.lower().replace(' ', '_'),
            pollutants=pollutants,
            model_name=model_name
        )
        
        return create_prediction_display(prediction, confidence, pollutants, is_realtime=False)
        
    except Exception as e:
        return create_error_display(f"Error: {str(e)}")

def get_live_pollutants(city):
    """
    Fetch real-time air quality data and return individual pollutant values.
    Used to pre-fill manual input fields.
    """
    try:
        city_key = city.lower().replace(' ', '_')
        data = collector.fetch_city_data(city_key)
        
        if not data:
            # Return current values or defaults if fetch fails
            return gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), gr.update()
        
        # Parse response to get pollutant dictionary
        parsed = collector.parse_api_response(data)
        
        return (
            parsed.get('pm2_5', 15.0),
            parsed.get('pm10', 25.0),
            parsed.get('no2', 10.0),
            parsed.get('o3', 30.0),
            parsed.get('co', 0.5),
            parsed.get('so2', 5.0),
            parsed.get('nh3', 2.0)
        )
    except Exception as e:
        print(f"Error fetching live data: {e}")
        return gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), gr.update()

def create_prediction_display(prediction, confidence, pollutants, is_realtime=False):
    """Create a formatted display for the prediction results."""
    color, emoji, category, health_msg = get_aqi_color_and_emoji(prediction)
    
    data_source = "🌐 Real-time API Data" if is_realtime else "✏️ Manual Input"
    
    # Calculate confidence interval width
    ci_width = confidence['upper'] - confidence['lower']
    ci_percentage = (ci_width / prediction * 100) if prediction > 0 else 0
    
    result_html = f"""
    <div style="font-family: 'Inter', sans-serif; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 15px; color: white; margin-bottom: 20px;">
        <p style="margin: 0; font-size: 14px; opacity: 0.9;">{data_source}</p>
        <h1 style="margin: 10px 0; font-size: 72px; font-weight: bold; text-align: center;">{emoji} {prediction:.2f}</h1>
        <h2 style="margin: 10px 0; font-size: 28px; text-align: center; font-weight: 600;">{category}</h2>
    </div>
    
    <div style="background: #f8fafc; border-radius: 12px; padding: 20px; margin-bottom: 20px; border-left: 4px solid {color};">
        <h3 style="margin-top: 0; color: #1e293b; font-size: 18px;">🏥 Health Implications</h3>
        <p style="color: #475569; line-height: 1.6; margin: 0;">{health_msg}</p>
    </div>
    
    <div style="background: #f8fafc; border-radius: 12px; padding: 20px; margin-bottom: 20px;">
        <h3 style="margin-top: 0; color: #1e293b; font-size: 18px;">📊 Prediction Confidence</h3>
        <div style="background: white; padding: 15px; border-radius: 8px; margin-bottom: 10px;">
            <p style="margin: 0 0 8px 0; color: #64748b; font-size: 14px;">Confidence Interval</p>
            <p style="margin: 0; font-size: 24px; font-weight: bold; color: #1e293b;">{confidence['lower']:.2f} - {confidence['upper']:.2f}</p>
        </div>
        <p style="color: #475569; line-height: 1.6; margin: 10px 0 0 0; font-size: 14px;">
            <strong>What does this mean?</strong> The model predicts the AQI is <strong>{prediction:.2f}</strong>, 
            but the true value is likely between <strong>{confidence['lower']:.2f}</strong> and <strong>{confidence['upper']:.2f}</strong>. 
            A narrower range (±{ci_width:.2f}) indicates higher confidence in the prediction.
        </p>
    </div>
    
    <div style="background: #f8fafc; border-radius: 12px; padding: 20px;">
        <h3 style="margin-top: 0; color: #1e293b; font-size: 18px;">🧪 Pollutant Levels</h3>
        <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px;">
            <div style="background: white; padding: 12px; border-radius: 8px;">
                <p style="margin: 0; color: #64748b; font-size: 12px;">PM2.5</p>
                <p style="margin: 4px 0 0 0; font-size: 18px; font-weight: bold; color: #1e293b;">{pollutants['pm2_5']:.2f} µg/m³</p>
            </div>
            <div style="background: white; padding: 12px; border-radius: 8px;">
                <p style="margin: 0; color: #64748b; font-size: 12px;">PM10</p>
                <p style="margin: 4px 0 0 0; font-size: 18px; font-weight: bold; color: #1e293b;">{pollutants['pm10']:.2f} µg/m³</p>
            </div>
            <div style="background: white; padding: 12px; border-radius: 8px;">
                <p style="margin: 0; color: #64748b; font-size: 12px;">NO₂</p>
                <p style="margin: 4px 0 0 0; font-size: 18px; font-weight: bold; color: #1e293b;">{pollutants['no2']:.2f} µg/m³</p>
            </div>
            <div style="background: white; padding: 12px; border-radius: 8px;">
                <p style="margin: 0; color: #64748b; font-size: 12px;">O₃</p>
                <p style="margin: 4px 0 0 0; font-size: 18px; font-weight: bold; color: #1e293b;">{pollutants['o3']:.2f} µg/m³</p>
            </div>
            <div style="background: white; padding: 12px; border-radius: 8px;">
                <p style="margin: 0; color: #64748b; font-size: 12px;">CO</p>
                <p style="margin: 4px 0 0 0; font-size: 18px; font-weight: bold; color: #1e293b;">{pollutants['co']:.2f} mg/m³</p>
            </div>
            <div style="background: white; padding: 12px; border-radius: 8px;">
                <p style="margin: 0; color: #64748b; font-size: 12px;">SO₂</p>
                <p style="margin: 4px 0 0 0; font-size: 18px; font-weight: bold; color: #1e293b;">{pollutants['so2']:.2f} µg/m³</p>
            </div>
            <div style="background: white; padding: 12px; border-radius: 8px;">
                <p style="margin: 0; color: #64748b; font-size: 12px;">NH₃</p>
                <p style="margin: 4px 0 0 0; font-size: 18px; font-weight: bold; color: #1e293b;">{pollutants['nh3']:.2f} µg/m³</p>
            </div>
        </div>
    </div>
    """
    
    return result_html

def create_error_display(error_message):
    """Create a formatted error display."""
    return f"""
    <div style="background: #fee2e2; border-left: 4px solid #ef4444; padding: 20px; border-radius: 8px;">
        <h3 style="margin-top: 0; color: #991b1b;">⚠️ Error</h3>
        <p style="color: #7f1d1d; margin: 0;">{error_message}</p>
    </div>
    """

# Define available cities and models
cities = ['Bangkok', 'Durban', 'Sao Paulo', 'Sydney', 'London', 'New York']
models = predictor.list_models()

# Custom CSS for better styling
custom_css = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');

.gradio-container {
    font-family: 'Inter', sans-serif !important;
}

.tab-nav button {
    font-size: 16px !important;
    font-weight: 600 !important;
    padding: 12px 24px !important;
}

.tab-nav button.selected {
    border-bottom: 3px solid #667eea !important;
}
"""

# Create Gradio Interface with Tabs
with gr.Blocks(title="City Air Quality Predictor", css=custom_css, theme=gr.themes.Soft()) as demo:
    gr.Markdown("""
    # 🌍 City Air Quality Index Predictor
    ### Predict air quality using real-time data or manual input with advanced ML models
    """)
    
    with gr.Tabs() as tabs:
        # Tab 1: Real-time Data
        with gr.Tab("🌐 Real-time Data"):
            gr.Markdown("""
            ### Get instant AQI predictions using live data from OpenWeatherMap API
            Select a city and model to fetch current pollutant levels and generate predictions automatically.
            """)
            
            with gr.Row():
                with gr.Column(scale=1):
                    rt_city_input = gr.Dropdown(
                        choices=cities, 
                        label="🏙️ Select City", 
                        value="London",
                        info="Choose a city to fetch real-time air quality data"
                    )
                    rt_model_input = gr.Dropdown(
                        choices=models, 
                        label="🤖 Select Model", 
                        value=models[0] if models else "xgboost",
                        info="XGBoost recommended for best accuracy"
                    )
                    rt_predict_btn = gr.Button("🔍 Fetch & Predict", variant="primary", size="lg")
                    
                    gr.Markdown("""
                    ---
                    ### 📖 About Real-time Mode
                    This mode automatically fetches current pollutant levels from the OpenWeatherMap API 
                    and generates predictions using your selected ML model.
                    
                    **Note:** Requires a valid OpenWeatherMap API key in your `.env` file.
                    """)
                
                with gr.Column(scale=2):
                    rt_output = gr.HTML(label="Prediction Result")
            
            rt_predict_btn.click(
                fn=fetch_realtime_data,
                inputs=[rt_city_input, rt_model_input],
                outputs=rt_output
            )
        
        # Tab 2: Manual Input
        with gr.Tab("✏️ Manual Input"):
            gr.Markdown("""
            ### Enter custom pollutant levels for AQI prediction
            Manually input pollutant concentrations to test different scenarios or when API access is unavailable.
            """)
            
            with gr.Row():
                with gr.Column(scale=1):
                    manual_city_input = gr.Dropdown(
                        choices=cities, 
                        label="🏙️ Select City", 
                        value="London"
                    )
                    manual_model_input = gr.Dropdown(
                        choices=models, 
                        label="🤖 Select Model", 
                        value=models[0] if models else "xgboost"
                    )
                    
                    load_live_btn = gr.Button("📥 Load Live Data", variant="secondary")
                    
                    gr.Markdown("### 🧪 Pollutant Levels")
                    
                    with gr.Row():
                        pm2_5_input = gr.Number(label="PM2.5 (µg/m³)", value=15.0, info="Fine particles")
                        pm10_input = gr.Number(label="PM10 (µg/m³)", value=25.0, info="Coarse particles")
                    
                    with gr.Row():
                        no2_input = gr.Number(label="NO₂ (µg/m³)", value=10.0, info="Nitrogen dioxide")
                        o3_input = gr.Number(label="O₃ (µg/m³)", value=30.0, info="Ozone")
                    
                    with gr.Row():
                        co_input = gr.Number(label="CO (mg/m³)", value=0.5, info="Carbon monoxide")
                        so2_input = gr.Number(label="SO₂ (µg/m³)", value=5.0, info="Sulfur dioxide")
                    
                    nh3_input = gr.Number(label="NH₃ (µg/m³)", value=2.0, info="Ammonia")
                    
                    manual_predict_btn = gr.Button("🔮 Predict AQI", variant="primary", size="lg")
                
                with gr.Column(scale=2):
                    manual_output = gr.HTML(label="Prediction Result")
            
            manual_predict_btn.click(
                fn=predict_aqi_manual,
                inputs=[manual_city_input, pm2_5_input, pm10_input, no2_input, o3_input, 
                       co_input, so2_input, nh3_input, manual_model_input],
                outputs=manual_output
            )

            load_live_btn.click(
                fn=get_live_pollutants,
                inputs=[manual_city_input],
                outputs=[pm2_5_input, pm10_input, no2_input, o3_input, co_input, so2_input, nh3_input]
            )
    
    # Footer with information
    gr.Markdown("""
    ---
    ### 📊 AQI Scale Reference
    
    | Range | Category | Color | Health Impact |
    |-------|----------|-------|---------------|
    | 0-1 | Good | 🟢 Green | Minimal risk |
    | 1-2 | Moderate | 🟡 Yellow | Acceptable for most |
    | 2-3 | Unhealthy for Sensitive Groups | 🟠 Orange | Sensitive groups may be affected |
    | 3-4 | Unhealthy | 🔴 Red | General public may be affected |
    | 4+ | Very Unhealthy / Hazardous | 🟣 Purple | Health alert for everyone |
    
    ---
    
    **Developed by Davide Ferreri** | [GitHub](https://github.com/DavideF99) | [LinkedIn](https://www.linkedin.com/in/davideferreri/)
    """)

if __name__ == "__main__":
    demo.launch()
