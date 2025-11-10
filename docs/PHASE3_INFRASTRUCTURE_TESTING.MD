# Phase 3 Infrastructure - Testing Guide

## 📋 What We Built

✅ **4 Production-Ready Scripts:**

1. `src/models/baseline_models.py` - Clean baseline model classes
2. `src/models/train.py` - Core training logic
3. `src/models/evaluate.py` - Evaluation and visualization
4. `scripts/train_models.py` - Command-line interface

---

## 🧪 Testing Steps

### **Step 1: Test Individual Components**

```bash
cd ~/Documents/GitHub/City-Air-Quality-Index-Predictor-with-Live-Data-Pipeline
source venv/bin/activate
```

**Test 1: Baseline Models**

```bash
python src/models/baseline_models.py
```

**Expected Output:**

- ✓ Creates synthetic test data
- ✓ Trains 3 baseline models
- ✓ Shows metrics for each
- ✓ No errors

**Test 2: Training Module**

```bash
python src/models/train.py
```

**Expected Output:**

- ✓ Checks for data files
- ✓ Trains all baselines if data exists
- ✓ Saves models and results
- ✓ Logs comprehensive metrics

**Test 3: Evaluation Module**

```bash
python src/models/evaluate.py
```

**Expected Output:**

- ✓ Loads saved results
- ✓ Generates comparison table
- ✓ Creates comparison plots
- ✓ Saves to visualizations/

---

### **Step 2: Train Models via CLI**

**Option A: Train All Baselines**

```bash
python scripts/train_models.py --model all-baselines --compare
```

**Option B: Train Specific Model**

```bash
python scripts/train_models.py --model linear --visualize
```

**Expected Results:**

- ✓ Models trained successfully
- ✓ Results saved to `data/models/`
- ✓ Comparison table generated
- ✓ Best model identified

---

### **Step 3: Verify Outputs**

**Check Saved Models:**

```bash
ls -lh data/models/
```

**Should see:**

- `persistence.joblib`
- `movingaverage-3.joblib`
- `movingaverage-7.joblib`
- `linearregression.joblib`
- `*_results.json` files
- `model_comparison.csv`

**Check Visualizations:**

```bash
ls -lh visualizations/models/
```

**Should see:**

- `*_predictions.png` - Actual vs predicted plots
- `*_errors.png` - Error analysis plots
- `*_importance.png` - Feature importance
- `model_comparison.png` - Model comparison

---

## 📊 Understanding the Output

### **Metrics Explained**

**RMSE (Root Mean Squared Error):**

- Average prediction error
- Lower is better
- Units: AQI units (1-5 scale)
- Good: < 0.5, Acceptable: 0.5-1.0

**MAE (Mean Absolute Error):**

- Average absolute error
- Lower is better
- More interpretable than RMSE
- Good: < 0.4, Acceptable: 0.4-0.8

**R² (R-squared):**

- Proportion of variance explained
- Higher is better (0 to 1)
- Good: > 0.7, Acceptable: 0.5-0.7

**Within 1 AQI:**

- Percentage of predictions within ±1 AQI unit
- Higher is better
- Good: > 80%

**Category Accuracy:**

- Predicts correct AQI category (1-5)
- Good: > 70%

---

## 🎯 Expected Baseline Performance

Based on your Phase 2 findings (top predictor: `aqi_lag_24h` with r=0.89):

**Persistence Model:**

- Val RMSE: ~0.6-0.8
- Should be decent (uses last value)

**Moving Average:**

- Val RMSE: ~0.5-0.7
- Slightly better (smooths noise)

**Linear Regression:**

- Val RMSE: ~0.4-0.6
- Best baseline (uses all features)
- Should have R² > 0.7

---

## 🔍 Troubleshooting

### **Issue: "Missing data files"**

**Problem:**

```
FileNotFoundError: Training data not found
```

**Solution:**
Run Phase 2 notebook first:

```bash
jupyter lab
# Open: notebooks/04_statistical_analysis.ipynb
# Run all cells to generate train/val/test data
```

---

### **Issue: "Module not found"**

**Problem:**

```
ModuleNotFoundError: No module named 'sklearn'
```

**Solution:**

```bash
pip install scikit-learn matplotlib seaborn scipy
```

---

### **Issue: Plots not showing**

**Problem:** No visualization windows appear

**Solution:**

- Plots are saved even if not displayed
- Check `visualizations/models/` directory
- Or use: `--visualize` flag to force generation

---

## ✅ Success Criteria

You know everything works if:

1. ✅ All 3 tests pass without errors
2. ✅ Models train and save successfully
3. ✅ Results JSON files created
4. ✅ Comparison table shows all models
5. ✅ Linear regression has best validation RMSE
6. ✅ Visualizations generated in `visualizations/models/`

---

## 🚀 Next Steps

Once infrastructure is tested:

### **Phase 3B: Tree-Based Models**

We'll create 3 new model files:

1. `src/models/random_forest_model.py`
2. `src/models/xgboost_model.py`
3. `src/models/lightgbm_model.py`

**The beauty:** All these will automatically work with:

- ✅ The training pipeline we just built
- ✅ The evaluation module
- ✅ The CLI script
- ✅ All visualizations

**To train them (after creation):**

```bash
python scripts/train_models.py --model random-forest --compare --visualize
python scripts/train_models.py --model xgboost --compare --visualize
python scripts/train_models.py --model lightgbm --compare --visualize
```

---

## 💡 Tips

**Quick Commands:**

```bash
# Train everything and compare
python scripts/train_models.py --model all-baselines --compare

# View comparison table
cat data/models/model_comparison.csv

# Check specific model results
cat data/models/linearregression_results.json | python -m json.tool

# Open visualizations
open visualizations/models/model_comparison.png
```

**Development Workflow:**

1. Test component individually
2. Test via CLI
3. Review results
4. Add new model
5. Repeat!

---

## 📝 Commands Summary

```bash
# Individual tests
python src/models/baseline_models.py
python src/models/train.py
python src/models/evaluate.py

# CLI training
python scripts/train_models.py --model all-baselines --compare --visualize

# View results
ls data/models/
ls visualizations/models/
cat data/models/model_comparison.csv
```

---

**Status:** Infrastructure Complete ✅  
**Ready for:** Tree-Based Models 🌲  
**Time to Complete:** 10-15 minutes testing
