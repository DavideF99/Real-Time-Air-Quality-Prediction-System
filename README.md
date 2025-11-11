# 🌍 Real-Time Air Quality Prediction System

Air pollution causes 7 million premature deaths annually (WHO). This ML system predicts Air Quality Index (AQI) levels 24 hours in advance using historical patterns and current conditions, helping citizens make informed decisions about outdoor activities and health precautions.

An end-to-end machine learning project that predicts Air Quality Index (AQI) levels 24 hours in advance using live environmental data.

## 🎯 Project Overview

This system collects real-time air quality data from 6 cities across 5 continents, builds predictive models, and serves predictions through a REST API and interactive dashboard.

## 🌆 Monitored Cities

- Bangkok, Thailand 🇹🇭
- Durban, South Africa 🇿🇦
- São Paulo, Brazil 🇧🇷
- Sydney, Australia 🇦🇺
- London, United Kingdom 🇬🇧
- New York City, United States 🇺🇸

## 🛠️ Technology Stack

- **Language:** Python 3.11
- **Data Processing:** Pandas, NumPy
- **API:** OpenWeatherMap Air Pollution API
- **Storage:** CSV → PostgreSQL (Phase 4)
- **ML Framework:** Scikit-learn, XGBoost
- **API:** FastAPI
- **Dashboard:** Streamlit
- **Deployment:** Docker, Railway/Render

## 📁 Project Structure

```
aqi-predictor/
├── data/              # Data storage
├── src/               # Source code
├── tests/             # Test suite
├── notebooks/         # Analysis notebooks
├── configs/           # Configuration files
└── scripts/           # Utility scripts
```

## 🚀 Setup Instructions

### Prerequisites

- Python 3.11+
- OpenWeatherMap API key

### Installation

1. Clone the repository

```bash
git clone <your-repo-url>
cd aqi-predictor
```

2. Create virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
```

3. Install dependencies

```bash
pip install -r requirements.txt
```

4. Configure environment

```bash
cp .env.example .env
# Edit .env and add your API key
```

## 📊 Project Status

- [x] Phase 1: Project Setup & Data Collection (In Progress)
- [x] Phase 2: Exploratory Data Analysis
- [x] Phase 3: Model Development
- [x] Phase 4: API Development
- [ ] Phase 5: Testing & Quality Assurance
- [ ] Phase 6: Deployment & Monitoring

## 📝 License

MIT License

## 👤 Author

https://github.com/DavideF99
