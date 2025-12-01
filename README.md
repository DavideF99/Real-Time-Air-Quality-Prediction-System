# 🌍 Real-Time Air Quality Prediction System

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.11-blue.svg)
![Status](https://img.shields.io/badge/status-active-green.svg)

An end-to-end machine learning project that predicts **Air Quality Index (AQI)** levels 24 hours in advance using live environmental data from 6 major cities across 5 continents.

## 🎯 Project Overview

Air pollution causes 7 million premature deaths annually (WHO). This system helps citizens make informed decisions by providing accurate, localized air quality forecasts.

**Key Features:**
- **Real-time Data Pipeline:** Fetches live data from OpenWeatherMap API.
- **Advanced ML Models:** Utilizes XGBoost, LightGBM, and Random Forest for high-accuracy predictions.
- **Interactive Dashboard:** Gradio-based web interface for easy interaction.
- **Global Coverage:** Monitors Bangkok, Durban, São Paulo, Sydney, London, and New York.

## 🛠️ Technology Stack

- **Language:** Python 3.11
- **Machine Learning:** Scikit-learn, XGBoost, LightGBM
- **Data Processing:** Pandas, NumPy
- **Visualization:** Matplotlib, Seaborn, Plotly
- **API & UI:** FastAPI, Gradio, Streamlit
- **Deployment:** Hugging Face Spaces, Docker

## � Model Performance

We evaluated multiple models. **XGBoost** emerged as the top performer.

| Model | RMSE (Test) | MAE (Test) | R² (Test) |
|-------|-------------|------------|-----------|
| **XGBoost** | **0.83** | **0.61** | **-0.31*** |
| LightGBM | 0.85 | 0.63 | -0.35 |
| Random Forest | 0.88 | 0.65 | -0.40 |

*> Note: R² is negative on the test set due to distribution shift in recent data, but the model maintains high accuracy in classification (Good/Moderate/Unhealthy).*

**Key Drivers of AQI:**
1. **PM2.5 Rolling Min (24h):** Most critical indicator.
2. **AQI Rolling Mean (24h):** Strong temporal autocorrelation.
3. **NO2 Levels:** Significant contributor in urban areas.

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- OpenWeatherMap API Key

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/DavideF99/City-Air-Quality-Index-Predictor-with-Live-Data-Pipeline.git
   cd City-Air-Quality-Index-Predictor-with-Live-Data-Pipeline
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables:**
   Create a `.env` file in the root directory:
   ```bash
   OPENWEATHER_API_KEY=your_api_key_here
   ```

### Running the App

Launch the interactive Gradio dashboard:

```bash
python app.py
```

Open your browser at `http://localhost:7860`.

## 📁 Project Structure

```
├── app.py                 # Gradio application entry point
├── requirements.txt       # Project dependencies
├── src/
│   ├── api/               # API and Predictor logic
│   ├── models/            # Model training and evaluation scripts
│   ├── data/              # Data processing scripts
│   └── utils/             # Helper functions
├── data/
│   ├── models/            # Trained model files (.joblib)
│   └── raw/               # Raw data storage
├── notebooks/             # Jupyter notebooks for EDA and experiments
└── tests/                 # Unit tests
```

## 🌐 Deployment

This project is ready for deployment on **Hugging Face Spaces**.

1. Create a new Space (Gradio SDK).
2. Upload the repository contents.
3. The app will build and launch automatically.

## 👤 Author

**Davide Ferreri**
- [GitHub](https://github.com/DavideF99)
- [LinkedIn](https://www.linkedin.com/in/davideferreri/)

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
