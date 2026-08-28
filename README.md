# LedgerMind AI — Multi-Source 3-Way Reconciliation & Exception Resolution Engine

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://ledgermind-dqkoh6evcwqlkkatlfajjj.streamlit.app/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Track: AI Finance Controller](https://img.shields.io/badge/Razorpay%20Buildathon-Track%2004-blueviolet.svg)](https://razorpay.com)

**Live Cloud Application:** [https://ledgermind-dqkoh6evcwqlkkatlfajjj.streamlit.app/](https://ledgermind-dqkoh6evcwqlkkatlfajjj.streamlit.app/)  
**GitHub Repository:** [https://github.com/Arunpurohit1766/Ledgermind-AI](https://github.com/Arunpurohit1766/Ledgermind-AI)  
**Submission Track:** Track 04 — AI Finance Controller (Razorpay AI Buildathon 2026)  
**Author:** Arun J (B.Tech Computer Science — Artificial Intelligence & Data Science)  

---

## 1. What LedgerMind AI Does (Executive Summary)

In digital commerce and fintech ecosystems, financial data is fragmented across three disconnected ledgers:
1. **Source 1: Internal Merchant Order DB** (Customer checkout amounts & payment instruments)
2. **Source 2: Payment Gateway Feed / Razorpay** (Contractual MDR fees, 18% statutory GST & net payout calculations)
3. **Source 3: Bank Realization Statements** (Actual cash credited with 12-digit UTR references)

### The Core Problem:
Silent fee rate overcharges (e.g. charging 2.8% instead of the contracted 1.9%), tax line miscalculations (28% luxury GST instead of statutory 18%), gateway risk escrow holds, and uncredited UTRs silently drain **1.5% to 3.5% of total gross revenue**. Traditional finance teams only discover these discrepancies weeks later through manual spreadsheet auditing.

### The LedgerMind AI Solution:
**LedgerMind AI** serves as an **Automated Finance Controller & Multi-Source Reconciliation Engine**:
* **High-Throughput 3-Way Relational Join:** Ingests and matches transactions across all 3 ledgers in milliseconds (<15 ms for 500 records; 552 ms for full 48k-record ledger joins at ~87.8k rec/sec).
* **Live Machine Learning Anomaly Risk Scoring:** Evaluates every transaction using an active, zero-leakage **XGBoost Classifier (0.8059 ROC-AUC / 0.3459 PR-AUC)** running 100% deterministically on 8 standard business features.
* **The Honest Exception List:** Transparently isolates non-matching records (MDR overcharges, GST tax bugs, escrow holds, and bank clearance lags) with root-cause diagnostics.
* **Audit-Ready Resolution Workflows:** Generates standard **GAAP Double-Entry Journal Proposals** (`DR 1140 Gateway Receivable / CR 5120 Fee Expense / CR 2210 GST Input Tax`) and compiles **API-Ready Dispute JSON Payloads** formatted for gateway dispute endpoints.

---

## 2. Transaction Lifecycle & Reconciliation Funnel

The relational database models the real-world drop-offs, gateway holds, and bank clearance pipeline across 50,000 enterprise transactions:

```
  50,000 Ingested Orders (Merchant DB)
       |
       +---> [ 972 FAILED ] (Bank network timeout / OTP failure)
       +---> [   513 REFUNDED ] (Customer order cancellations)
       |
       v
  48,515 SUCCESS Orders (Gateway Processing Batch)
       |
       +---> [   1,276 ON_HOLD ] (Gateway risk engine escrow hold)
       |
       v
  47,239 SETTLED Transactions (Cleared in Bank Account with 12-Digit UTR)
```

| Funnel Stage | Record Count | Percentage | Operational Meaning |
|---|---|---|---|
| **Total Ingested Orders** | 50,000 | 100.0% | Total customer checkout attempts in merchant database |
| **Failed / Declined** | 972 | 1.94% | Payment declined at acquiring bank / OTP stage |
| **Refunded Orders** | 513 | 1.03% | Order cancelled/returned, capital refunded to buyer |
| **Successful Orders** | 48,515 | 97.03% | Valid completed customer checkouts sent to Gateway |
| **Gateway Escrow Holds** | 1,276 | 2.55% | Payout delayed by Gateway risk/compliance engines |
| **Verified Bank Deposits** | 47,239 | 94.48% | Net cash cleared in merchant bank account with UTR |

---

## 3. End-to-End System Architecture

```
+---------------------------------------------------------------------------------------------------+
| 1. MULTI-SOURCE DATA INGESTION & RELATIONAL DATABASE LAYER (SQLite Relational Engine)       |
|    - orders (50,000 transaction records with amounts, timestamps, payment methods, categories)    |
|    - gateway_settlements (contract MDR rates, actual fees, 18% GST tax lines, settlement statuses) |
|    - bank_statements (UTR numbers, bank clearing timestamps, realized credit deposits)            |
|    - audit_ledger (audit logs, recovery journal entries, dispute payload metadata)                |
+-------------------------------------------------+-------------------------------------------------+
                                                  |
                                                  v
+---------------------------------------------------------------------------------------------------+
| 2. SCIKIT-LEARN PREPROCESSING & ML BENCHMARK PIPELINE (models/best_reconciliation_pipeline.joblib)|
|    - ColumnTransformer (StandardScaler for continuous signals + OneHotEncoder for categories)     |
|    - Class Imbalance Management (scale_pos_weight optimization for minority anomaly rate)         |
|    - Zero-Leakage Architecture (trained strictly on 8 standard business features)                 |
+-------------------------------------------------+-------------------------------------------------+
                                                  |
                                                  v
+---------------------------------------------------------------------------------------------------+
| 3. MULTI-MODEL BENCHMARK SUITE (models/benchmark_metrics.json)                                    |
|    - XGBoost Pipeline (0.8059 ROC-AUC | 0.3459 PR-AUC | 70.2% Recall) — Active Production        |
|    - Random Forest Ensemble (0.8061 ROC-AUC | 0.3412 PR-AUC | 66.9% Recall)                       |
|    - Logistic Regression (0.8135 ROC-AUC | 0.3436 PR-AUC | 73.0% Recall) — Linear Baseline           |
|    - Gradient Boosting (0.8171 ROC-AUC | 0.3590 PR-AUC)                                           |
+-------------------------------------------------+-------------------------------------------------+
                                                  |
                                                  v
+---------------------------------------------------------------------------------------------------+
| 4. EXECUTIVE COMMAND INTERFACE (Streamlit + UI/UX Pro Max Financial Trust Design System)         |
|    - Module 0: 3-Way System Architecture & Data Funnel (2-Minute Visual Walkthrough & Schema)     |
|    - Module 1: Multi-Source Batch Verification & Resolution Workflows (Active Inference & Drafing)|
|    - Module 2: Custom 3-File CSV Multi-Source Ingestion (In-Memory Staging for External Data)     |
|    - Module 3: Financial Stress Testing & MDR Sensitivity Simulator (EBITDA Scenario Modeling)    |
|    - Module 4: Machine Learning Benchmark & Zero-Leakage Pipeline Specification                   |
+---------------------------------------------------------------------------------------------------+
```

---

## 4. Multi-Source Reconciliation Workflow

### Module 0: 3-Way System Architecture & Data Funnel
- **2-Minute Visual Walkthrough:** Designed for evaluators and finance executives to understand how money flows between the Merchant, Gateway (Razorpay), and Bank (HDFC/ICICI).
- **Multi-Source Schema Inspector:** Inspect live data records across `orders`, `gateway_settlements`, `bank_statements`, and `audit_ledger`.

### Module 1: Multi-Source Batch Verification & Exception Resolution Workflows
- **3-Way Relational Join:** Ingests dynamic batches (50 to 48,515 records) joining Orders, Gateway settlements, and Bank UTRs in sub-second execution (<15 ms for 500 records; 552 ms for full 48k-record ledger).
- **Active ML Anomaly Scoring:** Uses the trained Scikit-learn XGBoost pipeline (`best_reconciliation_pipeline.joblib`) to score every transaction with a deterministic **AI Anomaly Risk Probability**.
- **The Honest Exception List:** Isolates non-matching records (MDR Overcharge, GST Miscalculation, Escrow Hold, Unrealized Bank Credit) with root-cause diagnostics.
- **Resolution Workflow & Journal Generation:** On 1-click execution:
  - Drafts GAAP-compliant **Double-Entry Journal Proposals**:
    - `DEBIT: 1140 Gateway Settlement Receivable` (Current Asset)
    - `CREDIT: 5120 Merchant Processing Fee Expense` (Expense Recovery)
    - `CREDIT: 2210 GST Input Tax Credit` (Tax Recovery)
  - Compiles standardized, **API-Ready Dispute JSON Payloads** formatted for gateway dispute endpoints.
  - Generates formal **Audit Defense Notices (.txt)** and models the **Projected 100.0% Reconciled State**.

### Module 2: Custom 3-File CSV Multi-Source Ingestion
- **External Evaluator Ingestion:** Drag-and-drop 3 independent raw CSV files (`orders.csv`, `gateway_settlements.csv`, `bank_statements.csv`) or download sample templates.
- **In-Memory Staging:** Mounts an in-memory SQLite database, executes live 3-way joins on `order_id` and `gateway_txn_id`, computes active ML anomaly scores, and provides 1-click download of the reconciled dataset.

### Module 3: Multi-Source Financial Stress & MDR Scenario Simulator
- Interactive sensitivity sliders for Credit Card MDR rates (0.5% to 3.5%), UPI volume share (20% to 80%), and Gateway Escrow Hold rates.
- Simulates gross fee variations and net EBITDA financial impact in real-time.

### Module 4: Machine Learning Benchmark & Zero-Leakage Pipeline
- Evaluates 4 ML architectures under realistic imbalanced class distribution without feature leakage.
- Direct ground-truth comparison table and mathematical specifications.

---

## 5. Machine Learning Pipeline & 8-Feature Deterministic Benchmark

### Deterministic Feature Design: Standard Business Signals Only
To ensure absolute reproducibility and avoid artificial synthetic assumptions (such as synthetic network latency or random traffic numbers), our machine learning model is trained **strictly on 8 standard business columns** that exist in every digital merchant's database:
1. `order_amount`: Raw transaction checkout amount in INR.
2. `log_amount`: Log-transformed transaction value (`log1p`).
3. `payment_method`: One-hot encoded payment instrument (`UPI`, `Credit Card`, `Debit Card`, `Net Banking`).
4. `merchant_category`: One-hot encoded business segment (`Gaming`, `Travel`, `Electronics`, `SaaS`, `Retail`, `Utilities`).
5. `contract_mdr_rate`: Contractual merchant discount rate baseline.
6. `order_hour`: Timestamp hour of day (0 to 23).
7. `is_high_value`: High-value transaction indicator (`order_amount > 10,000`).
8. `category_risk_prior`: Historical empirical risk factor by merchant sector.

*Zero random variables are used during inference — identical inputs always yield identical risk scores.*

### Verified Multi-Model Benchmark Leaderboard

| Model Architecture | ROC-AUC | PR-AUC (Baseline: 0.0980) | Precision | Recall | F1-Score | Model Role |
|---|---|---|---|---|---|---|
| **XGBoost (Active Production Primary)** | **0.8059** | **0.3459** (**3.53x Lift**) | **0.2367** | **70.2%** | **0.3541** | Active Real-Time Risk Scorer |
| **Random Forest Ensemble** | **0.8061** | **0.3412** (**3.48x Lift**) | **0.2458** | **66.9%** | **0.3595** | Balanced Tree Ensemble |
| **Logistic Regression (Linear Baseline)** | **0.8135** | **0.3436** (**3.51x Lift**) | **0.2389** | **73.0%** | **0.3600** | High-Sensitivity Early Screen |
| **Gradient Boosting** | **0.8171** | **0.3590** (**3.66x Lift**) | **0.6170** | **6.1%** | **0.1110** | High-Precision Conservative |

---

## 6. Core Banking System (CBS) GL Accounts & Double-Entry Mapping

When the Resolution Workflow engine executes, it drafts standard Core Banking System (CBS) General Ledger journal adjustments for finance review:

| Account Code | Account Name | Account Type | Normal Balance | Discrepancy Usage |
|---|---|---|---|---|
| **1140** | Gateway Settlement Receivable | Current Asset | Debit | Overcharged fees, held funds, and uncredited deposits claimable from gateway |
| **5120** | Merchant Processing Fee Expense | Operating Expense | Credit (Reversal) | Deduction reversal for excess MDR processing fees |
| **2210** | GST Input Tax Credit (ITC) | Current Asset / Liability | Credit (Reversal) | Tax line reversal for over-assessed 28% GST |
| **2050** | Gateway Escrow Suspense Clearing | Current Liability | Credit | Balancing suspense entry for funds on hold in gateway escrow |
| **1090** | Bank Inflow Clearing Suspense | Current Asset | Credit | Balancing suspense entry for unrealized bank credits or clearing shortfalls |
| **1145** | Unsettled Merchant Order Clearing | Current Asset | Debit | Holding account for merchant orders unacknowledged by gateway |
| **4010** | Sales Revenue Suspense | Revenue Suspense | Credit | Balancing entry for unconfirmed merchant order revenue |

*Every generated journal entry is guaranteed to be 100% mathematically balanced (Total Debits == Total Credits).*

---

## 7. Relational Database Schema Specification

```sql
-- 1. Orders Table (Merchant Primary DB)
CREATE TABLE orders (
    order_id VARCHAR(32) PRIMARY KEY,
    customer_id VARCHAR(32),
    order_amount DECIMAL(12,2),
    order_timestamp TIMESTAMP,
    payment_method VARCHAR(24),
    merchant_category VARCHAR(32),
    order_status VARCHAR(16)
);

-- 2. Gateway Settlements Table (Payment Gateway Feed)
CREATE TABLE gateway_settlements (
    settlement_id VARCHAR(32) PRIMARY KEY,
    order_id VARCHAR(32) REFERENCES orders(order_id),
    gateway_txn_id VARCHAR(32) UNIQUE,
    gross_amount DECIMAL(12,2),
    contract_mdr_rate DECIMAL(6,4),
    actual_fee_charged DECIMAL(12,2),
    gst_charged DECIMAL(12,2),
    net_settlement_amount DECIMAL(12,2),
    settlement_status VARCHAR(16),
    settlement_timestamp TIMESTAMP
);

-- 3. Bank Statements Table (Bank Realization Feed)
CREATE TABLE bank_statements (
    bank_txn_id VARCHAR(32) PRIMARY KEY,
    gateway_txn_id VARCHAR(32) REFERENCES gateway_settlements(gateway_txn_id),
    utr_number VARCHAR(32) UNIQUE,
    credit_amount DECIMAL(12,2),
    bank_timestamp TIMESTAMP,
    clearing_status VARCHAR(16)
);

-- 4. Audit Ledger Table (Resolution & Journal Audit Trail)
CREATE TABLE audit_ledger (
    audit_id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id VARCHAR(32) REFERENCES orders(order_id),
    anomaly_type VARCHAR(32),
    leakage_amount DECIMAL(12,2),
    ai_confidence REAL,
    root_cause_explanation TEXT,
    action_taken TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 8. Local Installation & Setup Guide

### Prerequisites
- Python 3.9 or higher
- Git

### 1. Clone the Repository
```bash
git clone https://github.com/Arunpurohit1766/Ledgermind-AI.git
cd Ledgermind-AI
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Launch the Application
```bash
python -m streamlit run app.py
```

The application will launch in your browser at `http://localhost:8501`.

---

## 9. Technology Stack

- **Frontend & Interface:** Streamlit (UI/UX Pro Max Financial Trust Design System, Obsidian Dark CSS)
- **Database Engine:** SQLite Relational Database v3.42 (In-process, sub-millisecond query execution)
- **Machine Learning:** Scikit-Learn Pipeline (`ColumnTransformer`, `StandardScaler`, `OneHotEncoder`), XGBoost, Random Forest, Joblib
- **Data Manipulation & Analytics:** Pandas, NumPy

---

## 10. Author & Submission Credentials

- **Author:** Arun J
- **Institution:** Swarnim Startup & Innovation University (SSIU), Ahmedabad
- **Program:** B.Tech Computer Science Engineering (Artificial Intelligence & Data Science)
- **Email:** `arunj.data1766@gmail.com`
- **GitHub:** [https://github.com/Arunpurohit1766](https://github.com/Arunpurohit1766)
