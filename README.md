---
title: City Air Quality Predictor
emoji: 🌍
colorFrom: blue
colorTo: green
sdk: gradio
sdk_version: 4.44.1
app_file: app.py
pinned: false
---

# 🌍 City Air Quality Index Predictor

An interactive machine learning application that predicts **Air Quality Index (AQI)** levels based on pollutant concentrations across 6 major global cities.

## 🎯 About

Air pollution causes 7 million premature deaths annually (WHO). This tool helps citizens make informed decisions by providing accurate air quality predictions using advanced machine learning models.

**Supported Cities:**
- 🇹🇭 Bangkok
- 🇿🇦 Durban
- 🇧🇷 São Paulo
- 🇦🇺 Sydney
- 🇬🇧 London
- 🇺🇸 New York

## 🤖 Models

Choose from multiple trained models:
- **XGBoost** (Recommended - Best Performance)
- **LightGBM**
- **Random Forest**

## 📊 Model Performance

| Model         | RMSE (Test) | MAE (Test) | R² (Test) |
| ------------- | ----------- | ---------- | --------- |
| **XGBoost**   | **0.83**    | **0.61**   | **-0.31** |
| LightGBM      | 0.85        | 0.63       | -0.35     |
| Random Forest | 0.88        | 0.65       | -0.40     |

## 🔬 How to Use

1. **Select a City** from the dropdown menu
2. **Choose a Model** (XGBoost recommended)
3. **Enter Pollutant Levels:**
   - **PM2.5** - Fine Particulate Matter (µg/m³)
   - **PM10** - Coarse Particulate Matter (µg/m³)
   - **NO2** - Nitrogen Dioxide (µg/m³)
   - **O3** - Ozone (µg/m³)
   - **CO** - Carbon Monoxide (mg/m³)
   - **SO2** - Sulfur Dioxide (µg/m³)
   - **NH3** - Ammonia (µg/m³)
4. **Click "Predict AQI"** to get the prediction

## 📈 AQI Categories

- **Good (0-1):** Air quality is satisfactory 🟢
- **Moderate (1-2):** Acceptable for most people 🟡
- **Unhealthy for Sensitive Groups (2-3):** May affect sensitive individuals 🟠
- **Unhealthy (3-4):** Everyone may experience health effects 🔴
- **Very Unhealthy / Hazardous (4+):** Health alert 🟣

## 🛠️ Technology Stack

- **Machine Learning:** XGBoost, LightGBM, Random Forest
- **Data Processing:** Pandas, NumPy, Scikit-learn
- **Interface:** Gradio
- **Deployment:** Hugging Face Spaces

## 👤 Author

**Davide Ferreri**

- [GitHub](https://github.com/DavideF99)
- [LinkedIn](https://www.linkedin.com/in/davideferreri/)
- [Full Project Repository](https://github.com/DavideF99/Real-Time-Air-Quality-Prediction-System)

## 📝 License

MIT License - See the full project repository for details.
