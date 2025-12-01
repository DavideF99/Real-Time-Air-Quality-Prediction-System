import gradio as gr
import pandas as pd
import numpy as np
from src.api.predictor import ModelPredictor
from pathlib import Path

# Initialize predictor
# We assume the app is run from the root directory
predictor = ModelPredictor()

def predict_aqi(city, pm2_5, pm10, no2, o3, co, so2, nh3, model_name):
    """
    Predict AQI based on input pollutants.
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
        
        # Determine AQI Category
        if prediction <= 1:
            category = "Good"
            color = "green"
        elif prediction <= 2:
            category = "Moderate"
            color = "yellow"
        elif prediction <= 3:
            category = "Unhealthy for Sensitive Groups"
            color = "orange"
        elif prediction <= 4:
            category = "Unhealthy"
            color = "red"
        else:
            category = "Very Unhealthy / Hazardous"
            color = "purple"
            
        result_str = f"""
        ### Predicted AQI: {prediction:.2f}
        **Category:** <span style="color:{color}">{category}</span>
        
        **Confidence Interval:** {confidence['lower']:.2f} - {confidence['upper']:.2f}
        """
        return result_str
        
    except Exception as e:
        return f"Error: {str(e)}"

# Define available cities and models
cities = ['Bangkok', 'Durban', 'Sao Paulo', 'Sydney', 'London', 'New York']
models = predictor.list_models()

# Create Gradio Interface
with gr.Blocks(title="City Air Quality Predictor") as demo:
    gr.Markdown("# 🌍 City Air Quality Index Predictor")
    gr.Markdown("Predict the Air Quality Index (AQI) based on pollutant levels and city.")
    
    with gr.Row():
        with gr.Column():
            city_input = gr.Dropdown(choices=cities, label="City", value="London")
            model_input = gr.Dropdown(choices=models, label="Model", value=models[0] if models else "xgboost")
            
            gr.Markdown("### Pollutant Levels")
            pm2_5_input = gr.Number(label="PM2.5", value=15.0)
            pm10_input = gr.Number(label="PM10", value=25.0)
            no2_input = gr.Number(label="NO2", value=10.0)
            o3_input = gr.Number(label="O3", value=30.0)
            co_input = gr.Number(label="CO", value=0.5)
            so2_input = gr.Number(label="SO2", value=5.0)
            nh3_input = gr.Number(label="NH3", value=2.0)
            
            predict_btn = gr.Button("Predict AQI", variant="primary")
            
        with gr.Column():
            output_markdown = gr.Markdown(label="Prediction Result")
            
            gr.Markdown("""
            ### About
            This tool uses machine learning models trained on historical air quality data to predict the AQI.
            
            **Pollutants:**
            - PM2.5, PM10: Particulate Matter
            - NO2: Nitrogen Dioxide
            - O3: Ozone
            - CO: Carbon Monoxide
            - SO2: Sulfur Dioxide
            - NH3: Ammonia
            """)

    predict_btn.click(
        fn=predict_aqi,
        inputs=[city_input, pm2_5_input, pm10_input, no2_input, o3_input, co_input, so2_input, nh3_input, model_input],
        outputs=output_markdown
    )

if __name__ == "__main__":
    demo.launch()
