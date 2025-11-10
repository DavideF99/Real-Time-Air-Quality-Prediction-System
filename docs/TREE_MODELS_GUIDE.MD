# Tree-Based Models - Complete Guide

## 🌲 What We Built

✅ **3 Advanced Models:**

1. **Random Forest** - Ensemble of decision trees
2. **XGBoost** - Extreme Gradient Boosting (often best!)
3. **LightGBM** - Fast gradient boosting from Microsoft

All integrate seamlessly with your existing infrastructure!

---

## 📦 Installation

### Install Required Libraries

```bash
cd ~/Documents/GitHub/City-Air-Quality-Index-Predictor-with-Live-Data-Pipeline
source venv/bin/activate

# Install tree-based libraries
pip install xgboost lightgbm

# Verify installation
python -c "import xgboost; import lightgbm; print('✓ All libraries installed!')"
```

---

## 🧪 Testing Individual Models

### Test 1: Random Forest

```bash
python src/models/random_forest_model.py
```

**Expected:**

- ✓ Creates synthetic data
- ✓ Trains 2 RF models (default, optimized)
- ✓ Shows metrics comparison
- ✓ Feature importance displayed

### Test 2: XGBoost

```bash
python src/models/xgboost_model.py
```

**Expected:**

- ✓ Trains XGBoost models
- ✓ Shows booster info
- ✓ Feature importance
- ✓ Faster than Random Forest

### Test 3: LightGBM

```bash
python src/models/lightgbm_model.py
```

**Expected:**

- ✓ Even faster training
- ✓ Similar accuracy to XGBoost
- ✓ Memory efficient

---

## 🚀 Training with Real Data

### Quick Start: Train All Models

```bash
# Train Random Forest
python scripts/train_models.py --model random-forest --compare --visualize

# Train XGBoost
python scripts/train_models.py --model xgboost --compare --visualize

# Train LightGBM
python scripts/train_models.py --model lightgbm --compare --visualize
```

### Compare Everything

After training all models, compare them:

```bash
python -c "
from src.models.evaluate import ModelEvaluator
evaluator = ModelEvaluator()
models = ['LinearRegression', 'RandomForest', 'XGBoost', 'LightGBM']
df = evaluator.compare_models(models)
print('\nBest Model:', df.iloc[0]['Model'])
"
```

---

## 📊 Expected Performance

Based on your Phase 2 findings (strong lag features, r=0.89):

### Baseline Performance (from Phase 3A)

- **Persistence:** Val RMSE ~0.6-0.8
- **Moving Average:** Val RMSE ~0.5-0.7
- **Linear Regression:** Val RMSE ~0.4-0.6

### Tree Models (Expected)

- **Random Forest:** Val RMSE ~0.3-0.5 (30-40% improvement)
- **XGBoost:** Val RMSE ~0.25-0.45 (best performer likely)
- **LightGBM:** Val RMSE ~0.25-0.45 (similar to XGBoost, faster)

### Why Tree Models Should Win

✅ **Non-linear patterns:** Trees capture complex relationships  
✅ **Feature interactions:** Automatic interaction detection  
✅ **Robust:** Handle outliers well  
✅ **Your data:** Strong lag features (trees excel with these)

---

## 🔍 Understanding the Models

### Random Forest 🌳

**How it works:**

- Builds 100+ independent trees
- Each tree trained on random data subset
- Final prediction = average of all trees

**Best for:**

- Stable, robust predictions
- When you need feature importance
- Good baseline for tree methods

**Hyperparameters:**

- `n_estimators`: Number of trees (100-500)
- `max_depth`: Tree depth limit (5-20)
- `min_samples_split`: Min samples to split (2-10)

---

### XGBoost ⚡

**How it works:**

- Builds trees sequentially
- Each tree corrects previous errors
- Gradient descent optimization
- Built-in regularization

**Best for:**

- Best accuracy (Kaggle winner!)
- Complex patterns
- When you need maximum performance

**Hyperparameters:**

- `n_estimators`: Boosting rounds (100-500)
- `max_depth`: Tree depth (3-10)
- `learning_rate`: Step size (0.01-0.3)
- `subsample`: Data sampling (0.5-1.0)

**Likely your best model!** 🏆

---

### LightGBM 🚀

**How it works:**

- Similar to XGBoost
- Leaf-wise tree growth (faster)
- Histogram-based splitting
- Optimized for speed

**Best for:**

- When XGBoost is too slow
- Large datasets
- Similar accuracy, faster training

**Hyperparameters:**

- `n_estimators`: Boosting rounds (100-500)
- `num_leaves`: Leaves per tree (20-50)
- `learning_rate`: Step size (0.01-0.3)

---

## 📈 Interpreting Results

### Key Metrics

**RMSE (Root Mean Squared Error):**

- Your main metric
- Penalizes large errors
- **Good:** < 0.4 AQI units
- **Excellent:** < 0.3 AQI units

**MAE (Mean Absolute Error):**

- Average error magnitude
- More interpretable
- **Good:** < 0.3 AQI units
- **Excellent:** < 0.25 AQI units

**R² (R-squared):**

- Variance explained
- **Good:** > 0.75
- **Excellent:** > 0.85

**Within 1 AQI:**

- Practical accuracy
- **Good:** > 85%
- **Excellent:** > 90%

### Overfitting Check

Compare Train vs Validation RMSE:

- **Difference < 5%:** ✓ Excellent generalization
- **Difference 5-20%:** ✓ Acceptable
- **Difference > 20%:** ⚠️ Overfitting!

---

## 🎯 Feature Importance

### View Top Features

```bash
# For any model
python -c "
from src.models.evaluate import ModelEvaluator
evaluator = ModelEvaluator()
evaluator.plot_feature_importance('XGBoost', top_n=20)
"
```

### Expected Top Features (from Phase 2)

1. `aqi_lag_24h` - Yesterday's AQI
2. `aqi_rolling_mean_24h` - 24h moving average
3. `pm2_5_lag_24h` - Yesterday's PM2.5
4. `aqi` - Current AQI
5. `aqi_rolling_mean_12h` - 12h moving average

If tree models show different top features, they've discovered new patterns!

---

## 🔧 Hyperparameter Tuning (Future)

After basic training, you can optimize:

### Grid Search Example

```python
from sklearn.model_selection import GridSearchCV
from src.models.xgboost_model import XGBoostModel

# Define parameter grid
param_grid = {
    'n_estimators': [100, 200, 300],
    'max_depth': [3, 5, 7],
    'learning_rate': [0.01, 0.05, 0.1]
}

# Run grid search
# (We'll implement this in Phase 3C)
```

---

## 📁 File Structure

After training, you'll have:

```
data/models/
├── persistence.joblib
├── movingaverage-3.joblib
├── linearregression.joblib
├── randomforest.joblib          ← NEW
├── xgboost.joblib                ← NEW
├── lightgbm.joblib               ← NEW
├── *_results.json
└── model_comparison.csv

visualizations/models/
├── randomforest_predictions.png  ← NEW
├── randomforest_errors.png       ← NEW
├── randomforest_importance.png   ← NEW
├── xgboost_predictions.png       ← NEW
├── xgboost_errors.png            ← NEW
├── xgboost_importance.png        ← NEW
├── lightgbm_predictions.png      ← NEW
├── lightgbm_errors.png           ← NEW
├── lightgbm_importance.png       ← NEW
└── model_comparison.png          ← UPDATED
```

---

## 🎓 Learning Tips

### Understanding Tree Models

**Decision Trees:**

- Split data based on features
- Create rules: "If PM2.5 > 30, then AQI = 3"
- Deep trees = complex rules

**Ensemble (Random Forest):**

- Many trees vote
- Reduces overfitting
- More stable predictions

**Boosting (XGBoost, LightGBM):**

- Trees correct each other
- Focus on hard examples
- Usually best accuracy

### When to Use Each

**Use Random Forest when:**

- You want interpretability
- You need robust predictions
- You're starting with tree methods

**Use XGBoost when:**

- You want best accuracy
- You have time for tuning
- You can wait for training

**Use LightGBM when:**

- XGBoost is too slow
- You have many features
- Training time matters

---

## 🐛 Troubleshooting

### Issue: "XGBoost not installed"

```bash
pip install xgboost
# If that fails:
conda install -c conda-forge xgboost
```

### Issue: "LightGBM not installed"

```bash
pip install lightgbm
# If that fails:
conda install -c conda-forge lightgbm
```

### Issue: Training too slow

**Random Forest:**

- Reduce `n_estimators` (100 → 50)
- Limit `max_depth` (None → 10)

**XGBoost/LightGBM:**

- Reduce `n_estimators` (100 → 50)
- Increase `learning_rate` (0.1 → 0.3)

### Issue: Overfitting (Val >> Train RMSE)

**Random Forest:**

- Increase `min_samples_split` (2 → 5)
- Reduce `max_depth`
- Use fewer features (`max_features='sqrt'`)

**XGBoost/LightGBM:**

- Add regularization (`reg_alpha=0.1, reg_lambda=1.0`)
- Reduce `learning_rate` + increase `n_estimators`
- Use `subsample=0.8, colsample_bytree=0.8`

---

## ✅ Success Checklist

After training all tree models:

- [ ] All 3 models train without errors
- [ ] XGBoost/LightGBM outperform Linear Regression
- [ ] Tree models show Val RMSE < 0.5
- [ ] Feature importance makes sense
- [ ] Visualizations generated
- [ ] Model comparison table created
- [ ] Best model identified

---

## 🚀 Next Steps

### Phase 3C: Model Optimization (Optional)

1. **Hyperparameter tuning**

   - Grid search
   - Random search
   - Bayesian optimization

2. **Ensemble methods**

   - Stack models
   - Blend predictions
   - Weighted averaging

3. **Feature engineering refinement**
   - Remove low-importance features
   - Create new interactions
   - Optimize feature selection

### Phase 4: Deployment (Coming Soon)

1. **API Development** (FastAPI)
2. **Web Dashboard** (Streamlit)
3. **Real-time predictions**
4. **Model serving**

---

## 💡 Pro Tips

**Tip 1: Always compare to baselines**

- If trees don't beat Linear Regression, investigate!
- Check for bugs, data leakage, or issues

**Tip 2: Trust your validation set**

- Test set is for final evaluation only
- Optimize based on validation performance

**Tip 3: Feature importance is gold**

- Reveals what model learned
- Can simplify model (remove low-importance features)
- Validates domain knowledge

**Tip 4: Visualize predictions**

- Scatter plots show patterns
- Residual plots reveal systematic errors
- Error by city/time shows weak spots

**Tip 5: Document everything**

- Note best hyperparameters
- Save reasoning for decisions
- Portfolio gold!

---

## 📊 Quick Commands Reference

```bash
# Train all tree models
python scripts/train_models.py --model random-forest --compare
python scripts/train_models.py --model xgboost --compare
python scripts/train_models.py --model lightgbm --compare

# Compare all models
python -c "
from src.models.evaluate import ModelEvaluator
evaluator = ModelEvaluator()
all_models = ['Persistence', 'LinearRegression', 'RandomForest', 'XGBoost', 'LightGBM']
evaluator.compare_models(all_models)
"

# View results
cat data/models/model_comparison.csv

# Best model
head -2 data/models/model_comparison.csv | tail -1
```

---

**Status:** Tree Models Complete ✅  
**Expected Best:** XGBoost or LightGBM 🏆  
**Time to Train:** 5-10 minutes all models  
**Next:** Model optimization (optional) or Phase 4 (deployment)
