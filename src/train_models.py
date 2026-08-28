import sqlite3
import os
import json
import numpy as np
import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import roc_auc_score, average_precision_score, precision_score, recall_score, f1_score

try:
    from xgboost import XGBClassifier
    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False

def load_clean_data(db_path, random_state=42):
    print(f"Connecting to SQLite database: {db_path}")
    conn = sqlite3.connect(db_path)
    conn.execute('PRAGMA foreign_keys = ON;')
    
    query = """
    SELECT 
        o.order_id,
        o.order_amount,
        o.payment_method,
        o.merchant_category,
        o.order_timestamp,
        g.contract_mdr_rate,
        CASE 
            WHEN g.settlement_status = 'ON_HOLD' THEN 1
            WHEN (g.actual_fee_charged - (o.order_amount * g.contract_mdr_rate)) > 5.0 THEN 1
            WHEN (g.gst_charged / (g.actual_fee_charged + 1e-5)) > 0.22 THEN 1
            ELSE 0 
        END as is_financial_anomaly
    FROM orders o
    JOIN gateway_settlements g ON o.order_id = g.order_id
    WHERE o.order_status = 'SUCCESS';
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    # 8 Clean, Deterministic Business Features
    df['order_hour'] = pd.to_datetime(df['order_timestamp']).dt.hour
    df['is_high_value'] = (df['order_amount'] > 10000).astype(int)
    df['log_amount'] = np.log1p(df['order_amount'])
    
    category_risk_map = {'Gaming': 0.8, 'Travel': 0.7, 'Electronics': 0.5, 'SaaS': 0.3, 'Retail': 0.2, 'Utilities': 0.1}
    df['category_risk_prior'] = df['merchant_category'].map(category_risk_map).fillna(0.25)
    
    return df

def train_realistic_benchmarks():
    project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(project_dir, 'data', 'financial_ledger.db')
    models_dir = os.path.join(project_dir, 'models')
    os.makedirs(models_dir, exist_ok=True)
    
    df = load_clean_data(db_path)
    
    num_features = ['order_amount', 'log_amount', 'contract_mdr_rate', 'order_hour', 'is_high_value', 'category_risk_prior']
    cat_features = ['payment_method', 'merchant_category']
    target = 'is_financial_anomaly'
    
    X = df[num_features + cat_features]
    y = df[target].values
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.20, random_state=42, stratify=y)
    
    print(f"Training on {len(X_train):,} rows, Testing on {len(X_test):,} rows | Anomaly Prevalence: {y.mean()*100:.2f}%")
    
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', StandardScaler(), num_features),
            ('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), cat_features)
        ]
    )
    
    X_train_trans = preprocessor.fit_transform(X_train)
    X_test_trans = preprocessor.transform(X_test)
    
    benchmark_results = {}
    
    # 1. Logistic Regression Baseline
    print("Training Logistic Regression...")
    clf_lr = LogisticRegression(class_weight='balanced', max_iter=1000, random_state=42)
    clf_lr.fit(X_train_trans, y_train)
    probs_lr = clf_lr.predict_proba(X_test_trans)[:, 1]
    preds_lr = (probs_lr >= 0.50).astype(int)
    
    benchmark_results['Logistic Regression'] = {
        'ROC_AUC': round(float(roc_auc_score(y_test, probs_lr)), 4),
        'PR_AUC': round(float(average_precision_score(y_test, probs_lr)), 4),
        'Precision': round(float(precision_score(y_test, preds_lr, zero_division=0)), 4),
        'Recall': round(float(recall_score(y_test, preds_lr, zero_division=0)), 4),
        'F1_Score': round(float(f1_score(y_test, preds_lr, zero_division=0)), 4),
        'Type': 'Classical Linear ML'
    }
    
    # 2. Random Forest Ensemble
    print("Training Random Forest...")
    clf_rf = RandomForestClassifier(n_estimators=100, max_depth=10, class_weight='balanced', random_state=42, n_jobs=-1)
    clf_rf.fit(X_train_trans, y_train)
    probs_rf = clf_rf.predict_proba(X_test_trans)[:, 1]
    preds_rf = (probs_rf >= 0.50).astype(int)
    
    benchmark_results['Random Forest'] = {
        'ROC_AUC': round(float(roc_auc_score(y_test, probs_rf)), 4),
        'PR_AUC': round(float(average_precision_score(y_test, probs_rf)), 4),
        'Precision': round(float(precision_score(y_test, preds_rf, zero_division=0)), 4),
        'Recall': round(float(recall_score(y_test, preds_rf, zero_division=0)), 4),
        'F1_Score': round(float(f1_score(y_test, preds_rf, zero_division=0)), 4),
        'Type': 'Ensemble Trees'
    }
    
    # 3. Gradient Boosting Classifier
    print("Training Gradient Boosting...")
    clf_gb = GradientBoostingClassifier(n_estimators=100, max_depth=5, learning_rate=0.08, random_state=42)
    clf_gb.fit(X_train_trans, y_train)
    probs_gb = clf_gb.predict_proba(X_test_trans)[:, 1]
    preds_gb = (probs_gb >= 0.50).astype(int)
    
    benchmark_results['Gradient Boosting'] = {
        'ROC_AUC': round(float(roc_auc_score(y_test, probs_gb)), 4),
        'PR_AUC': round(float(average_precision_score(y_test, probs_gb)), 4),
        'Precision': round(float(precision_score(y_test, preds_gb, zero_division=0)), 4),
        'Recall': round(float(recall_score(y_test, preds_gb, zero_division=0)), 4),
        'F1_Score': round(float(f1_score(y_test, preds_gb, zero_division=0)), 4),
        'Type': 'Ensemble Boosting'
    }
    
    # 4. XGBoost Classifier (Optimized)
    if HAS_XGBOOST:
        print("Training XGBoost Classifier (Scale Pos Weight Tuned)...")
        pos_scale = (len(y_train) - y_train.sum()) / (y_train.sum() + 1e-5)
        clf_xgb = XGBClassifier(scale_pos_weight=pos_scale, n_estimators=120, max_depth=6, learning_rate=0.08, random_state=42, eval_metric='logloss')
        clf_xgb.fit(X_train_trans, y_train)
        probs_xgb = clf_xgb.predict_proba(X_test_trans)[:, 1]
        preds_xgb = (probs_xgb >= 0.50).astype(int)
        
        benchmark_results['XGBoost'] = {
            'ROC_AUC': round(float(roc_auc_score(y_test, probs_xgb)), 4),
            'PR_AUC': round(float(average_precision_score(y_test, probs_xgb)), 4),
            'Precision': round(float(precision_score(y_test, preds_xgb, zero_division=0)), 4),
            'Recall': round(float(recall_score(y_test, preds_xgb, zero_division=0)), 4),
            'F1_Score': round(float(f1_score(y_test, preds_xgb, zero_division=0)), 4),
            'Type': 'Gradient Boosted Trees (Optimized)'
        }
        
    winning_model = clf_xgb if HAS_XGBOOST else clf_rf
    best_pipeline = Pipeline([
        ('preprocessor', preprocessor),
        ('model', winning_model)
    ])
    joblib.dump(best_pipeline, os.path.join(models_dir, 'best_reconciliation_pipeline.joblib'))
    
    with open(os.path.join(models_dir, 'benchmark_metrics.json'), 'w') as f:
        json.dump(benchmark_results, f, indent=4)
        
    print("\n--- 8-FEATURE CLEAN ZERO-LEAKAGE BENCHMARK SCORES ---")
    results_df = pd.DataFrame(benchmark_results).T
    print(results_df.to_string())

if __name__ == '__main__':
    train_realistic_benchmarks()
