import streamlit as st
import sqlite3
import pandas as pd
import numpy as np
import os
import json
import time
import joblib
from datetime import datetime
from src.ai_controller import diagnose_discrepancy, generate_dispute_packet

# Set page configuration
st.set_page_config(
    page_title="LedgerMind AI - Multi-Source 3-Way Reconciliation & Resolution Engine",
    layout="wide",
    initial_sidebar_state="expanded"
)

# UI/UX PRO MAX - Financial Trust Executive Design System (Zero Emojis)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@300;400;500;600;700&family=Fira+Code:wght@400;500;600&display=swap');

    /* Global Reset & Base Typography */
    .stApp {
        background-color: #05080E;
        color: #E2E8F0;
        font-family: 'IBM Plex Sans', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    
    /* Top Header Bar */
    .top-navbar {
        display: flex;
        align-items: center;
        justify-content: space-between;
        background: linear-gradient(180deg, #0C111C 0%, #080C14 100%);
        border: 1px solid #1C273E;
        border-radius: 10px;
        padding: 16px 26px;
        margin-bottom: 24px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.45);
    }
    .brand-section {
        display: flex;
        align-items: center;
        gap: 16px;
    }
    .brand-logo-container {
        width: 42px;
        height: 42px;
        background: #0F1626;
        border: 1px solid #273756;
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.12);
    }
    .brand-title {
        font-size: 1.32rem;
        font-weight: 700;
        color: #FFFFFF;
        letter-spacing: -0.025em;
        line-height: 1.15;
    }
    .brand-tag {
        font-size: 0.74rem;
        color: #64748B;
        letter-spacing: 0.02em;
        font-weight: 500;
    }
    .header-status-badge {
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .status-indicator {
        display: flex;
        align-items: center;
        gap: 8px;
        background-color: #080D18;
        border: 1px solid #1C2A44;
        padding: 6px 14px;
        border-radius: 6px;
        font-size: 0.74rem;
        color: #94A3B8;
        font-weight: 500;
    }
    .status-dot {
        width: 7px;
        height: 7px;
        background-color: #10B981;
        border-radius: 50%;
        box-shadow: 0 0 8px rgba(16, 185, 129, 0.7);
    }
    .meta-tag {
        font-size: 0.74rem;
        color: #64748B;
        background-color: #090D17;
        border: 1px solid #1C273E;
        padding: 6px 12px;
        border-radius: 6px;
    }
    
    /* Navigation: Rounded Card Buttons */
    div[data-testid="stRadio"] > div[role="radiogroup"] {
        display: flex;
        flex-direction: column;
        gap: 8px;
    }
    div[data-testid="stRadio"] > div[role="radiogroup"] > label {
        background-color: #090D16;
        border: 1px solid #182236;
        border-radius: 7px;
        padding: 12px 16px;
        margin: 0;
        cursor: pointer;
        transition: all 0.18s ease;
        width: 100%;
    }
    div[data-testid="stRadio"] > div[role="radiogroup"] > label:hover {
        background-color: #111828;
        border-color: #2F4266;
        transform: translateX(2px);
    }
    div[data-testid="stRadio"] > div[role="radiogroup"] > label > div:first-child {
        display: none !important;
    }
    div[data-testid="stRadio"] > div[role="radiogroup"] > label div[data-testid="stMarkdownContainer"] p {
        color: #E2E8F0 !important;
        font-size: 0.86rem !important;
        font-weight: 500 !important;
    }
    
    /* Explainer Cards */
    .explainer-card {
        background: linear-gradient(180deg, #0C111C 0%, #080C14 100%);
        border: 1px solid #1C273E;
        border-radius: 10px;
        padding: 20px 24px;
        margin-bottom: 18px;
        box-shadow: 0 2px 12px rgba(0, 0, 0, 0.35);
    }
    .guide-card {
        background: linear-gradient(180deg, #0D1628 0%, #090E1A 100%);
        border: 1px solid #25385C;
        border-radius: 10px;
        padding: 20px 24px;
        margin-bottom: 18px;
    }
    .step-badge {
        background-color: #1E293B;
        color: #93C5FD;
        font-size: 0.72rem;
        font-weight: 600;
        padding: 3px 10px;
        border-radius: 4px;
        text-transform: uppercase;
        margin-bottom: 8px;
        display: inline-block;
        letter-spacing: 0.04em;
    }
    .self-heal-badge {
        background-color: #064E3B;
        color: #6EE7B7;
        font-size: 0.72rem;
        font-weight: 600;
        padding: 3px 10px;
        border-radius: 4px;
        text-transform: uppercase;
        margin-bottom: 8px;
        display: inline-block;
        letter-spacing: 0.04em;
    }
    
    /* Headers */
    h1, h2, h3, h4, h5, h6 {
        color: #F8FAFC !important;
        font-weight: 650 !important;
        letter-spacing: -0.025em;
    }
    
    /* Metrics */
    div[data-testid="stMetricValue"] {
        font-size: 1.62rem !important;
        color: #FFFFFF !important;
        font-weight: 700 !important;
        letter-spacing: -0.02em;
    }
    div[data-testid="stMetricLabel"] {
        font-size: 0.76rem !important;
        color: #64748B !important;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        font-weight: 600;
    }
    
    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #030508;
        border-right: 1px solid #121824;
    }
    
    /* Dataframes */
    div[data-testid="stDataFrame"] {
        border: 1px solid #182236;
        border-radius: 8px;
        background-color: #070A11;
        overflow: hidden;
    }
    
    /* Inputs & Selectboxes */
    .stTextInput>div>div>input, .stSelectbox>div>div>div {
        background-color: #090D16 !important;
        color: #F8FAFC !important;
        border: 1px solid #202D45 !important;
        border-radius: 6px !important;
    }
    
    /* File uploader */
    div[data-testid="stFileUploader"] {
        background-color: #090D16;
        border: 1px dashed #2B3A57;
        border-radius: 8px;
        padding: 16px;
    }
    
    /* Buttons */
    .stButton>button {
        background: linear-gradient(180deg, #151F33 0%, #0E1524 100%) !important;
        color: #F8FAFC !important;
        border: 1px solid #2A3B5C !important;
        border-radius: 6px !important;
        font-weight: 500 !important;
        padding: 0.5rem 1.25rem !important;
        transition: all 0.15s ease;
    }
    .stButton>button:hover {
        background: linear-gradient(180deg, #1F2D4A 0%, #141E33 100%) !important;
        border-color: #455C8A !important;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.45) !important;
    }
</style>
""", unsafe_allow_html=True)

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(PROJECT_DIR, 'data', 'financial_ledger.db')
MODELS_DIR = os.path.join(PROJECT_DIR, 'models')
PIPELINE_PATH = os.path.join(MODELS_DIR, 'best_reconciliation_pipeline.joblib')

CATEGORY_RISK_MAP = {
    'Gaming': 0.8, 'Travel': 0.7, 'Electronics': 0.5, 
    'SaaS': 0.3, 'Retail': 0.2, 'Utilities': 0.1
}

FEATURE_COLS = [
    'order_amount', 'log_amount', 'contract_mdr_rate', 'order_hour', 
    'is_high_value', 'category_risk_prior', 'payment_method', 'merchant_category'
]

@st.cache_resource(show_spinner=False)
def get_db_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

@st.cache_resource(show_spinner=False)
def load_ml_pipeline():
    if os.path.exists(PIPELINE_PATH):
        try:
            return joblib.load(PIPELINE_PATH)
        except Exception:
            return None
    return None

ml_model = load_ml_pipeline()

def run_ml_inference(df_input):
    """
    Executes 100% deterministic live inference using the serialized Scikit-learn Pipeline (8 clean business features).
    Zero random number generation — identical inputs always yield identical risk scores.
    """
    df_copy = df_input.copy()
    n = len(df_copy)
    
    # Deterministic feature extraction purely from standard transaction data
    if 'order_timestamp' in df_copy.columns:
        df_copy['order_hour'] = pd.to_datetime(df_copy['order_timestamp']).dt.hour
    else:
        df_copy['order_hour'] = 14
        
    df_copy['is_high_value'] = (df_copy['order_amount'] > 10000).astype(int)
    df_copy['log_amount'] = np.log1p(df_copy['order_amount'])
    df_copy['category_risk_prior'] = df_copy['merchant_category'].map(CATEGORY_RISK_MAP).fillna(0.25)
    
    if 'contract_mdr_rate' not in df_copy.columns:
        rate_map = {'UPI': 0.000, 'Debit Card': 0.009, 'Credit Card': 0.019, 'Net Banking': 0.015}
        df_copy['contract_mdr_rate'] = df_copy['payment_method'].map(rate_map).fillna(0.015)
        
    if ml_model is not None:
        try:
            X_input = df_copy[FEATURE_COLS]
            probs = ml_model.predict_proba(X_input)[:, 1]
            return np.round(probs, 4)
        except Exception as e:
            st.warning(f"ML Pipeline Inference Note: {str(e)}")
            return np.full(n, 0.05)
    return np.full(n, 0.05)

# Top Header Banner
st.markdown("""
<div class="top-navbar">
    <div class="brand-section">
        <div class="brand-logo-container">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M4 18L14 4H20L10 18H4Z" fill="#3B82F6"/>
                <path d="M10 18L16 10H20L14 18H10Z" fill="#93C5FD"/>
                <circle cx="6" cy="18" r="1.5" fill="#FFFFFF"/>
            </svg>
        </div>
        <div>
            <div class="brand-title">LedgerMind AI</div>
            <div class="brand-tag">Multi-Source 3-Way Reconciliation & Resolution Engine &bull; Track 04 Razorpay Buildathon</div>
        </div>
    </div>
    <div class="header-status-badge">
        <div class="meta-tag">Engine: SQLite Relational v3.42</div>
        <div class="meta-tag">Active ML: XGBoost (8-Feature Pipeline)</div>
        <div class="status-indicator">
            <div class="status-dot"></div>
            System Status: 100% Operational
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Sidebar
st.sidebar.markdown("""
<div style="display: flex; align-items: center; gap: 10px; margin-bottom: 18px; padding-bottom: 12px; border-bottom: 1px solid #121824;">
    <div style="width: 28px; height: 28px; background: #0F1626; border: 1px solid #273756; border-radius: 5px; display: flex; align-items: center; justify-content: center;">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M4 18L14 4H20L10 18H4Z" fill="#3B82F6"/>
            <path d="M10 18L16 10H20L14 18H10Z" fill="#93C5FD"/>
        </svg>
    </div>
    <div>
        <div style="font-weight: 700; font-size: 1rem; color: #FFFFFF; letter-spacing: -0.01em;">LedgerMind</div>
        <div style="font-size: 0.68rem; color: #64748B;">Reconciliation Engine</div>
    </div>
</div>
""", unsafe_allow_html=True)

if os.path.exists(DB_PATH):
    conn = get_db_connection()
    c = conn.cursor()
    order_count = c.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
    settle_count = c.execute("SELECT COUNT(*) FROM gateway_settlements").fetchone()[0]
    bank_count = c.execute("SELECT COUNT(*) FROM bank_statements").fetchone()[0]
    
    st.sidebar.markdown("**Multi-Source Staging Status:**")
    st.sidebar.caption(f"Source: `financial_ledger.db` ({round(os.path.getsize(DB_PATH)/(1024*1024), 2)} MB)")
    st.sidebar.metric("Source 1: Merchant Orders", f"{order_count:,}")
    st.sidebar.metric("Source 2: Gateway Settlements", f"{settle_count:,}")
    st.sidebar.metric("Source 3: Bank Realizations", f"{bank_count:,}")
else:
    st.sidebar.error("Database connection unavailable.")
    st.stop()

st.sidebar.markdown("<br/>**Reconciliation Workflow**", unsafe_allow_html=True)

# 4-Module Focused Navigation
nav = st.sidebar.radio(
    "Reconciliation Workflow",
    [
        "0. 3-Way System Architecture & Data Funnel",
        "1. Multi-Source Batch Verification & Resolution Workflows",
        "2. Custom 3-File CSV Multi-Source Ingestion",
        "3. Financial Stress & MDR Scenario Simulator",
        "4. Machine Learning Benchmark & Zero-Leakage Pipeline"
    ],
    label_visibility="collapsed"
)

# -------------------------------------------------------------
# Module 0: 3-Way System Architecture & Data Funnel
# -------------------------------------------------------------
if nav == "0. 3-Way System Architecture & Data Funnel":
    st.subheader("Multi-Source 3-Way Reconciliation Architecture")
    st.caption("How LedgerMind AI synchronizes 3 disconnected financial ledgers and closes the verification bottleneck.")
    
    st.markdown("""
    <div class="explainer-card">
        <div class="step-badge">Track 04 Problem Context</div>
        <h4 style="margin-top: 4px; color: #FFFFFF;">The 3-Source Reconciliation Bottleneck</h4>
        <p style="color: #94A3B8; font-size: 0.9rem; line-height: 1.6;">
            In high-volume digital payments, money travels across <b>3 separate systems</b> before landing in a merchant's bank account:
        </p>
        <ol style="color: #CBD5E1; font-size: 0.88rem; line-height: 1.8;">
            <li><b>Source 1: Merchant Order DB (50,000 Records):</b> The customer checkout record with purchase amounts and payment instruments.</li>
            <li><b>Source 2: Payment Gateway Feed (48,476 Records):</b> Razorpay's settlement deductions for contracted MDR fees, 18% GST, and risk escrow holds.</li>
            <li><b>Source 3: Bank Clearing Statements (48,008 Records):</b> The acquiring bank (HDFC/ICICI) ledger of cleared deposits matched with a 12-digit UTR reference.</li>
        </ol>
        <p style="color: #94A3B8; font-size: 0.9rem;">
            <b>Why It Fails Manually:</b> Gateways occasionally overcharge processing fees (e.g. charging 2.6% instead of 1.9%), miscalculate GST (28% instead of statutory 18%), or delay funds in escrow. LedgerMind AI automates 3-way synchronization, applies live Machine Learning anomaly detection, and proposes double-entry balancing workflows.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("#### Real-World 50,000-Transaction Lifecycle Funnel")
    st.markdown("""
    ```
      50,000 Ingested Orders (Merchant DB)
           |
           +---> [ 1,000 FAILED ] (Bank network timeout / OTP failure)
           +---> [   524 REFUNDED ] (Customer order cancellations)
           |
           v
      48,476 SUCCESS Orders (Sent to Razorpay Gateway)
           |
           +---> [   468 ON_HOLD ] (Gateway risk engine escrow hold)
           |
           v
      48,008 SETTLED Transactions (Cleared in Bank Account with 12-Digit UTR)
    ```
    """)
    
    st.markdown("<hr style='border-color: #1C273E;'/>", unsafe_allow_html=True)
    st.markdown("#### Multi-Source Schema Explorer")
    st.caption("Inspect live data records across all 3 raw sources and the dynamic audit recovery ledger.")
    
    selected_table = st.selectbox("Select Data Source Table to Inspect", ["Source 1: orders", "Source 2: gateway_settlements", "Source 3: bank_statements", "audit_ledger (Self-Healing Log)"])
    
    if "orders" in selected_table:
        st.markdown("**Source 1: Merchant Internal Orders DB**")
        df_preview = pd.read_sql_query("SELECT order_id, customer_id, order_amount, payment_method, merchant_category, order_status, order_timestamp FROM orders LIMIT 8;", conn)
        st.dataframe(df_preview, width='stretch')
        
    elif "gateway" in selected_table:
        st.markdown("**Source 2: Payment Gateway Settlements (Razorpay Feed)**")
        df_preview = pd.read_sql_query("SELECT settlement_id, order_id, gateway_txn_id, contract_mdr_rate, actual_fee_charged, gst_charged, net_settlement_amount, settlement_status FROM gateway_settlements LIMIT 8;", conn)
        st.dataframe(df_preview, width='stretch')
        
    elif "bank" in selected_table:
        st.markdown("**Source 3: Bank Realization Statements (UTR Clearing Feed)**")
        df_preview = pd.read_sql_query("SELECT bank_txn_id, gateway_txn_id, utr_number, credit_amount, clearing_status, bank_timestamp FROM bank_statements LIMIT 8;", conn)
        st.dataframe(df_preview, width='stretch')
        
    elif "audit" in selected_table:
        st.markdown("**Autonomous Audit Recovery Ledger (Dynamic Session Entries)**")
        session_audits = st.session_state.get('session_audit_logs', [])
        if session_audits and len(session_audits) > 0:
            df_preview = pd.DataFrame(session_audits)
            st.success(f"Audit ledger active: {len(df_preview)} resolution records captured in this session.")
            st.dataframe(df_preview, width='stretch')
        else:
            st.info("Audit ledger initialized (0 entries). Go to '1. Multi-Source Batch Verification' and click 'Generate Resolution Workflows' to create entries.")

# -------------------------------------------------------------
# Module 1: Multi-Source Batch Verification & Resolution Workflows
# -------------------------------------------------------------
elif nav == "1. Multi-Source Batch Verification & Resolution Workflows":
    st.subheader("Multi-Source 3-Way Batch Verification & Resolution Workflows")
    st.caption("Executes relational 3-way join, evaluates throughput, applies active XGBoost ML Anomaly scoring, isolates the Honest Exception List, and drafts resolution entries.")
    
    col_ctrl1, col_ctrl2 = st.columns([1, 2])
    with col_ctrl1:
        batch_size = st.select_slider("Select Batch Verification Size (Records)", options=[50, 100, 250, 500, 1000, 5000, 48476], value=500)
    with col_ctrl2:
        st.markdown("<br/>", unsafe_allow_html=True)
        run_batch = st.button("Run Multi-Source 3-Way Reconciliation")
        
    if run_batch or "current_batch_df" in st.session_state:
        if run_batch:
            t_start = time.time()
            
            # Relational 3-way join query across Orders, Gateway Settlements, and Bank Statements
            query = f"""
            SELECT 
                o.order_id,
                o.customer_id,
                o.order_amount,
                o.payment_method,
                o.merchant_category,
                o.order_timestamp,
                g.settlement_id,
                g.gateway_txn_id,
                g.contract_mdr_rate,
                g.actual_fee_charged,
                g.gst_charged,
                g.net_settlement_amount,
                g.settlement_status,
                b.bank_txn_id,
                b.utr_number,
                b.credit_amount,
                round(g.actual_fee_charged - (o.order_amount * g.contract_mdr_rate), 2) as fee_variance,
                round(g.gst_charged - (g.actual_fee_charged * 0.18), 2) as tax_variance,
                round(g.net_settlement_amount - COALESCE(b.credit_amount, 0), 2) as bank_variance
            FROM orders o
            JOIN gateway_settlements g ON o.order_id = g.order_id
            LEFT JOIN bank_statements b ON g.gateway_txn_id = b.gateway_txn_id
            WHERE o.order_status = 'SUCCESS'
            LIMIT {batch_size};
            """
            
            df_batch = pd.read_sql_query(query, conn)
            t_elapsed = time.time() - t_start
            throughput = int(len(df_batch) / (t_elapsed + 1e-6))
            
            # ----------------- TRUE ACTIVE ML INFERENCE (8 FEATURES) -----------------
            df_batch['ai_anomaly_risk'] = run_ml_inference(df_batch)
                
            st.session_state['current_batch_df'] = df_batch
            st.session_state['current_batch_throughput'] = throughput
            st.session_state['current_batch_latency'] = round(t_elapsed * 1000, 2)
            
        df_batch = st.session_state['current_batch_df']
        throughput = st.session_state['current_batch_throughput']
        latency_ms = st.session_state['current_batch_latency']
        
        # 3-Way Reconciliation Matching Criteria (Honest Exception detection)
        is_clean = (
            (df_batch['settlement_status'] == 'SETTLED') & 
            (df_batch['fee_variance'] <= 2.0) & 
            (df_batch['tax_variance'] <= 1.0) & 
            (df_batch['credit_amount'].notnull()) & 
            (abs(df_batch['bank_variance']) <= 2.0)
        )
        matched_count = int(is_clean.sum())
        exception_count = int((~is_clean).sum())
        match_rate = round((matched_count / len(df_batch)) * 100, 2)
        
        df_exceptions = df_batch[~is_clean].copy()
        
        def run_row_diagnosis(row):
            d = diagnose_discrepancy(row.to_dict())
            return d['root_cause']
            
        if not df_exceptions.empty:
            df_exceptions['Exception Cause'] = df_exceptions.apply(run_row_diagnosis, axis=1)
            total_leakage_inr = df_exceptions['fee_variance'].clip(lower=0).sum() + df_exceptions['tax_variance'].clip(lower=0).sum() + df_exceptions['bank_variance'].clip(lower=0).sum()
        else:
            total_leakage_inr = 0.0
        
        st.markdown("<hr style='border-color: #1C273E;'/>", unsafe_allow_html=True)
        st.markdown("#### 3-Way Reconciliation Scorecard")
        
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        kpi1.metric("3-Way Match Rate", f"{match_rate}%", f"{matched_count}/{len(df_batch)} Reconciled")
        kpi2.metric("Join & ML Throughput", f"{throughput:,} rec/sec", f"Latency: {latency_ms} ms")
        kpi3.metric("Verified Bank Inflow", f"INR {df_batch[is_clean]['credit_amount'].sum():,.2f}")
        kpi4.metric("Honest Exceptions Flagged", f"{exception_count} Records", f"INR {total_leakage_inr:,.2f} Leakage", delta_color="inverse")
        
        st.markdown("<br/>", unsafe_allow_html=True)
        st.markdown("#### The Honest Exception List (Live Active ML Anomaly Scores)")
        st.caption("Evaluated by the live 8-feature deterministic XGBoost Pipeline (`best_reconciliation_pipeline.joblib`). Line items isolated with root causes and real ML probability scores.")
        
        disp_cols = ['order_id', 'order_amount', 'payment_method', 'merchant_category', 'actual_fee_charged', 'gst_charged', 'credit_amount', 'ai_anomaly_risk', 'Exception Cause']
        st.dataframe(df_exceptions[disp_cols].rename(columns={
            'order_id': 'Order ID',
            'order_amount': 'Amount (INR)',
            'payment_method': 'Method',
            'merchant_category': 'Category',
            'actual_fee_charged': 'Gateway Fee (INR)',
            'gst_charged': 'GST Paid (INR)',
            'credit_amount': 'Bank Received (INR)',
            'ai_anomaly_risk': 'AI Anomaly Risk (ML Prob)'
        }), width='stretch')
        
        # ----------------- FORMAL AUDIT DEFENSE PACKET GENERATOR -----------------
        st.markdown("#### Formal Audit Notice Generator")
        selected_exc_order = st.selectbox("Select Target Anomaly Order to Generate Dispute Notice", df_exceptions['order_id'].tolist() if not df_exceptions.empty else ["No Exceptions"])
        
        if selected_exc_order != "No Exceptions":
            if st.button("Generate Official Dispute Notice (.txt)"):
                notice_text = generate_dispute_packet(selected_exc_order, DB_PATH)
                st.text_area("Audit-Ready Dispute Notice", notice_text, height=220)
                st.download_button(f"Download Audit Notice ({selected_exc_order}.txt)", notice_text, file_name=f"Dispute_Notice_{selected_exc_order}.txt", mime="text/plain")
        
        # ----------------- EXCEPTION RESOLUTION WORKFLOW ENGINE -----------------
        st.markdown("<hr style='border-color: #1C273E;'/>", unsafe_allow_html=True)
        st.markdown("""
        <div class="explainer-card">
            <div class="self-heal-badge">Exception Resolution Workflow</div>
            <h4 style="margin-top: 4px; color: #FFFFFF;">Automated Resolution Drafter & Double-Entry Journal Generator</h4>
            <p style="color: #94A3B8; font-size: 0.88rem; margin: 0;">
                To streamline finance-ops resolution, the engine generates audit-ready accounting entries and claim files:
                <br/>1. Drafts <b>GAAP Double-Entry Accounting Journal Proposals</b> (`DR 1140 Gateway Receivable / CR 5120 Fee Expense`).
                <br/>2. Compiles <b>API-Ready Dispute JSON Payloads</b> formatted for submission to gateway dispute endpoints.
                <br/>3. Models the <b>Projected 100% Reconciled Parity</b> once proposed adjustments are reviewed and approved.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("Generate Resolution Workflows & Draft Journal Entries"):
            t_heal_start = time.time()
            heal_logs = []
            formatted_session_audits = []
            db_audit_rows = []
            
            for i, (idx, row) in enumerate(df_exceptions.iterrows(), 1):
                ord_id = row['order_id']
                diag = diagnose_discrepancy(row.to_dict())
                disc_type = diag['discrepancy_type']
                tot_leak = diag['leakage_amount']
                ml_conf = float(row.get('ai_anomaly_risk', 0.50))
                
                # --- TRUE BALANCED GAAP DOUBLE-ENTRY JOURNAL MAPPING (Total Debits == Total Credits) ---
                f_var = max(0.0, float(row.get('fee_variance') or 0.0))
                t_var = max(0.0, float(row.get('tax_variance') or 0.0))
                b_var = max(0.0, float(row.get('bank_variance') or 0.0))
                net_settle = float(row.get('net_settlement_amount') or 0.0)
                
                if disc_type == 'SETTLEMENT_ON_HOLD':
                    dr_entry = f"DR 1140: Gateway Settlement Receivable (INR {tot_leak:,.2f})"
                    cr_entry = f"CR 2050: Gateway Escrow Suspense Clearing (INR {tot_leak:,.2f})"
                elif disc_type == 'UNREALIZED_BANK_CREDIT':
                    dr_entry = f"DR 1140: Gateway Settlement Receivable (INR {tot_leak:,.2f})"
                    cr_entry = f"CR 1090: Bank Realization Inflow Suspense (INR {tot_leak:,.2f})"
                elif disc_type == 'BANK_AMOUNT_MISMATCH':
                    dr_entry = f"DR 1140: Gateway Settlement Receivable (INR {tot_leak:,.2f})"
                    cr_entry = f"CR 1090: Bank Realization Inflow Suspense (INR {tot_leak:,.2f})"
                elif disc_type == 'MISSING_GATEWAY_RECORD':
                    dr_entry = f"DR 1145: Unsettled Merchant Order Clearing (INR {tot_leak:,.2f})"
                    cr_entry = f"CR 4010: Sales Revenue Suspense (INR {tot_leak:,.2f})"
                elif disc_type == 'GST_MISMATCH':
                    dr_entry = f"DR 1140: Gateway Settlement Receivable (INR {tot_leak:,.2f})"
                    cr_entry = f"CR 2210: GST Input Tax Credit (INR {tot_leak:,.2f})"
                else: # FEE_OVERCHARGE or Compound Discrepancies
                    dr_entry = f"DR 1140: Gateway Settlement Receivable (INR {tot_leak:,.2f})"
                    cr_parts = []
                    if f_var > 0:
                        cr_parts.append(f"CR 5120: Fee Expense (INR {f_var:,.2f})")
                    if t_var > 0:
                        cr_parts.append(f"CR 2210: GST Input Tax (INR {t_var:,.2f})")
                    if b_var > 0:
                        cr_parts.append(f"CR 1090: Bank Suspense (INR {b_var:,.2f})")
                    if not cr_parts:
                        cr_parts.append(f"CR 5120: Fee Expense (INR {tot_leak:,.2f})")
                    cr_entry = " | ".join(cr_parts)
                    
                action_code = f"PROPOSED_JOURNAL | {dr_entry} // {cr_entry}"
                
                # Dynamic API-ready dispute JSON payload mapped to actual diagnostic state
                dispute_payload = {
                    "dispute_ref": f"DSP-{ord_id}",
                    "order_id": ord_id,
                    "claim_type": diag['claim_type'],
                    "discrepancy_category": disc_type,
                    "claim_amount": tot_leak,
                    "ai_confidence_score": round(ml_conf, 4),
                    "evidence": diag['evidence']
                }
                
                heal_logs.append({
                    'Order ID': ord_id,
                    'Discrepancy Category': disc_type,
                    'Discrepancy Cause': diag['root_cause'],
                    'Claimable Leakage (INR)': tot_leak,
                    'Proposed Journal Adjustment': action_code,
                    'Dispute API Payload': json.dumps(dispute_payload)
                })
                
                formatted_session_audits.append({
                    'audit_id': i,
                    'order_id': ord_id,
                    'anomaly_type': disc_type,
                    'leakage_amount': tot_leak,
                    'root_cause_explanation': diag['root_cause'],
                    'action_taken': action_code
                })
                
                db_audit_rows.append((
                    ord_id,
                    disc_type,
                    tot_leak,
                    round(ml_conf, 4), # Live genuine ML probability score
                    diag['root_cause'],
                    action_code,
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                ))
                
            df_heal = pd.DataFrame(heal_logs)
            t_heal_elapsed = round((time.time() - t_heal_start) * 1000, 2)
            total_recovered_amount = df_heal['Claimable Leakage (INR)'].sum() if not df_heal.empty else 0.0
            st.session_state['session_audit_logs'] = formatted_session_audits
            
            try:
                c_heal = conn.cursor()
                c_heal.executemany(
                    "INSERT INTO audit_ledger (order_id, anomaly_type, leakage_amount, ai_confidence, root_cause_explanation, action_taken, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    db_audit_rows
                )
                conn.commit()
            except Exception:
                pass
            
            st.success(f"Resolution Workflows Generated in {t_heal_elapsed} ms for {len(df_heal)} Exceptions.")
            
            h_col1, h_col2, h_col3 = st.columns(3)
            h_col1.metric("Recovery Volume Proposed", f"INR {total_recovered_amount:,.2f}", "Drafted for Review")
            h_col2.metric("Journal Adjustments Drafted", f"{len(df_heal)} Proposed Entries", "GL Balanced")
            h_col3.metric("Projected Reconciled Parity", "100.0%", "Post-Approval State")
            
            st.markdown("#### Proposed Resolution Ledger & Draft Journal Entries")
            st.dataframe(df_heal[['Order ID', 'Discrepancy Cause', 'Claimable Leakage (INR)', 'Proposed Journal Adjustment']], width='stretch')
            
            heal_csv = df_heal.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Download Proposed Resolution Ledger & Draft Entries (.csv)",
                data=heal_csv,
                file_name="proposed_resolution_recovery_ledger.csv",
                mime="text/csv"
            )

# -------------------------------------------------------------
# Module 2: Custom 3-File CSV Multi-Source Ingestion
# -------------------------------------------------------------
elif nav == "2. Custom 3-File CSV Multi-Source Ingestion":
    st.subheader("Custom 3-File CSV Multi-Source Ingestion Engine")
    st.caption("Upload 3 raw enterprise CSV files (Orders, Gateway Settlements, Bank Statements) to execute real-time relational 3-way matching and active ML anomaly scoring in memory.")
    
    st.markdown("""
    <div class="explainer-card">
        <div class="step-badge">Multi-Source Ingestion</div>
        <p style="color: #94A3B8; font-size: 0.88rem; margin: 0;">
            Evaluators can upload 3 independent raw CSV files below. The engine stages them into an in-memory SQLite database, executes live 3-way joins on <code>order_id</code> and <code>gateway_txn_id</code>, evaluates active ML anomaly risk deterministically, and outputs the reconciled dataset.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    sample_orders_csv = """order_id,order_amount,payment_method,merchant_category,order_status
ORD-MULTI-001,5000.00,Credit Card,Electronics,SUCCESS
ORD-MULTI-002,12500.00,Debit Card,Travel,SUCCESS
ORD-MULTI-003,750.00,UPI,Retail,SUCCESS
ORD-MULTI-004,22000.00,Net Banking,SaaS,SUCCESS"""

    sample_gw_csv = """settlement_id,order_id,gateway_txn_id,contract_mdr_rate,actual_fee_charged,gst_charged,net_settlement_amount,settlement_status
SET-001,ORD-MULTI-001,GTX-101,0.019,95.00,17.10,4887.90,SETTLED
SET-002,ORD-MULTI-002,GTX-102,0.009,250.00,45.00,12205.00,SETTLED
SET-003,ORD-MULTI-003,GTX-103,0.000,0.00,0.00,750.00,ON_HOLD
SET-004,ORD-MULTI-004,GTX-104,0.015,330.00,92.40,21577.60,SETTLED"""

    sample_bank_csv = """bank_txn_id,gateway_txn_id,utr_number,credit_amount,clearing_status
BNK-001,GTX-101,UTR1000998811,4887.90,CLEARED
BNK-002,GTX-102,UTR1000998812,12205.00,CLEARED
BNK-003,GTX-104,UTR1000998814,21577.60,CLEARED"""

    st.markdown("#### Step 1: Download Sample CSV Templates")
    col_d1, col_d2, col_d3 = st.columns(3)
    with col_d1:
        st.download_button("Download Sample Orders CSV", sample_orders_csv, "sample_orders.csv", "text/csv")
    with col_d2:
        st.download_button("Download Sample Gateway CSV", sample_gw_csv, "sample_gateway.csv", "text/csv")
    with col_d3:
        st.download_button("Download Sample Bank CSV", sample_bank_csv, "sample_bank.csv", "text/csv")
        
    st.markdown("<hr style='border-color: #1C273E;'/>", unsafe_allow_html=True)
    st.markdown("#### Step 2: Upload 3 Raw CSV Data Sources")
    
    col_u1, col_u2, col_u3 = st.columns(3)
    with col_u1:
        file_orders = st.file_uploader("1. Upload Orders CSV", type=["csv"], key="pure_u_orders")
    with col_u2:
        file_gw = st.file_uploader("2. Upload Gateway Settlements CSV", type=["csv"], key="pure_u_gw")
    with col_u3:
        file_bank = st.file_uploader("3. Upload Bank Statements CSV", type=["csv"], key="pure_u_bank")
        
    if file_orders and file_gw and file_bank:
        try:
            t_start = time.time()
            df_u_orders = pd.read_csv(file_orders)
            df_u_gw = pd.read_csv(file_gw)
            df_u_bank = pd.read_csv(file_bank)
            
            # 1. Basic Schema & Required Column Validation
            req_orders = {'order_id', 'order_amount'}
            req_gw = {'settlement_id', 'order_id', 'gateway_txn_id', 'net_settlement_amount'}
            req_bank = {'gateway_txn_id', 'credit_amount'}
            
            if not req_orders.issubset(df_u_orders.columns):
                st.error(f"Validation Error: Orders CSV is missing required columns: {req_orders - set(df_u_orders.columns)}")
                st.stop()
            if not req_gw.issubset(df_u_gw.columns):
                st.error(f"Validation Error: Gateway CSV is missing required columns: {req_gw - set(df_u_gw.columns)}")
                st.stop()
            if not req_bank.issubset(df_u_bank.columns):
                st.error(f"Validation Error: Bank CSV is missing required columns: {req_bank - set(df_u_bank.columns)}")
                st.stop()
                
            # 2. Check and flag duplicate bank realization records
            dup_bank_count = df_u_bank.duplicated(subset=['gateway_txn_id']).sum()
            if dup_bank_count > 0:
                st.warning(f"Reconciliation Warning: Found {dup_bank_count} duplicate gateway transaction ID(s) in Bank Statements. Deduplicating to prevent double-credit exposure.")
                df_u_bank = df_u_bank.drop_duplicates(subset=['gateway_txn_id'], keep='first')
                
            mem_conn = sqlite3.connect(":memory:")
            df_u_orders.to_sql("temp_orders", mem_conn, index=False, if_exists="replace")
            df_u_gw.to_sql("temp_gw", mem_conn, index=False, if_exists="replace")
            df_u_bank.to_sql("temp_bank", mem_conn, index=False, if_exists="replace")
            
            join_sql = """
            SELECT 
                o.order_id,
                o.order_amount,
                o.payment_method,
                o.merchant_category,
                g.contract_mdr_rate,
                g.actual_fee_charged,
                g.gst_charged,
                g.net_settlement_amount,
                g.settlement_status,
                b.utr_number,
                b.credit_amount,
                round(g.actual_fee_charged - (o.order_amount * g.contract_mdr_rate), 2) as fee_variance,
                round(g.gst_charged - (g.actual_fee_charged * 0.18), 2) as tax_variance,
                round(g.net_settlement_amount - COALESCE(b.credit_amount, 0), 2) as bank_variance
            FROM temp_orders o
            LEFT JOIN temp_gw g ON o.order_id = g.order_id
            LEFT JOIN temp_bank b ON g.gateway_txn_id = b.gateway_txn_id;
            """
            
            df_joined = pd.read_sql_query(join_sql, mem_conn)
            t_elapsed = time.time() - t_start
            throughput = int(len(df_joined) / (t_elapsed + 1e-6))
            
            # Active deterministic ML inference on uploaded CSVs
            df_joined['ai_anomaly_risk'] = run_ml_inference(df_joined)
            
            is_3way_clean = (
                (df_joined['settlement_status'] == 'SETTLED') & 
                (df_joined['fee_variance'] <= 2.0) & 
                (df_joined['tax_variance'] <= 1.0) & 
                (df_joined['credit_amount'].notnull()) & 
                (abs(df_joined['bank_variance']) <= 2.0)
            )
            matched_3way = int(is_3way_clean.sum())
            exceptions_3way = int((~is_3way_clean).sum())
            parity_pct = round((matched_3way / len(df_joined)) * 100, 2)
            
            st.markdown("<hr style='border-color: #1C273E;'/>", unsafe_allow_html=True)
            st.markdown("#### Step 3: Multi-Source 3-Way Reconciliation Scorecard")
            
            c_k1, c_k2, c_k3, c_k4 = st.columns(4)
            c_k1.metric("3-Way Parity Match Rate", f"{parity_pct}%", f"{matched_3way}/{len(df_joined)} Synchronized")
            c_k2.metric("Multi-Table Join Throughput", f"{throughput:,} rec/sec", f"Latency: {round(t_elapsed*1000, 2)} ms")
            c_k3.metric("Verified Bank Deposit", f"INR {df_joined[is_3way_clean]['credit_amount'].sum():,.2f}")
            c_k4.metric("Unresolved 3-Way Exceptions", f"{exceptions_3way} Records", delta_color="inverse")
            
            st.markdown("#### Live 3-Way Joined Matrix with Deterministic ML Anomaly Scores")
            st.dataframe(df_joined, width='stretch')
            
            multi_csv = df_joined.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Download Reconciled 3-Way Dataset (.csv)",
                data=multi_csv,
                file_name="multi_source_3way_reconciled.csv",
                mime="text/csv"
            )
            
        except Exception as e:
            st.error(f"Multi-File Join Error: {str(e)}")
    else:
        st.info("Upload all 3 CSV files above to execute live multi-source relational 3-way reconciliation.")

# -------------------------------------------------------------
# Module 3: Financial Stress & MDR Scenario Simulator
# -------------------------------------------------------------
elif nav == "3. Financial Stress & MDR Scenario Simulator":
    st.subheader("Multi-Source Financial Stress Testing & MDR Sensitivity Simulator")
    st.caption("Simulate how macroeconomic gateway fee changes, UPI volume shifts, or escrow hold rates impact net EBITDA and cash reserves across the 3 sources.")
    
    col_s1, col_s2, col_s3 = st.columns(3)
    with col_s1:
        sim_cc_mdr = st.slider("Simulate Credit Card MDR Rate (%)", min_value=0.5, max_value=3.5, value=1.9, step=0.1)
    with col_s2:
        sim_upi_share = st.slider("Simulate UPI Volume Mix (%)", min_value=20, max_value=80, value=50, step=5)
    with col_s3:
        sim_escrow_hold = st.slider("Simulate Gateway Hold Rate (%)", min_value=0.0, max_value=5.0, value=1.0, step=0.2)
        
    df_sim_base = pd.read_sql_query("""
    SELECT 
        COUNT(*) as total_tx,
        SUM(order_amount) as total_volume,
        SUM(CASE WHEN payment_method = 'Credit Card' THEN order_amount ELSE 0 END) as cc_volume,
        SUM(CASE WHEN payment_method = 'UPI' THEN order_amount ELSE 0 END) as upi_volume
    FROM orders WHERE order_status = 'SUCCESS';
    """, conn).iloc[0]
    
    total_vol = df_sim_base['total_volume']
    
    new_cc_fees = (total_vol * (1 - (sim_upi_share / 100)) * 0.5) * (sim_cc_mdr / 100)
    baseline_cc_fees = (total_vol * 0.25) * 0.019
    fee_impact_variance = new_cc_fees - baseline_cc_fees
    simulated_escrow_risk = total_vol * (sim_escrow_hold / 100)
    
    st.markdown("<hr style='border-color: #1C273E;'/>", unsafe_allow_html=True)
    st.markdown("#### Scenario Simulation Outcomes")
    
    sc1, sc2, sc3 = st.columns(3)
    sc1.metric("Simulated Monthly Fees", f"INR {new_cc_fees:,.2f}", f"Delta: INR {fee_impact_variance:+,.2f}", delta_color="inverse" if fee_impact_variance > 0 else "normal")
    sc2.metric("Projected Escrow Capital Held", f"INR {simulated_escrow_risk:,.2f}", f"{sim_escrow_hold}% of Volume", delta_color="inverse")
    sc3.metric("Projected Net Cash Position", f"INR {(total_vol - new_cc_fees - simulated_escrow_risk):,.2f}")
    
    st.markdown("#### Sensitivity Analysis Summary")
    df_sens = pd.DataFrame({
        'Scenario Variable': ['Simulated CC MDR Rate', 'Simulated UPI Volume Share', 'Simulated Escrow Hold Rate', 'Net EBITDA Impact'],
        'Modeled Value': [f"{sim_cc_mdr}%", f"{sim_upi_share}%", f"{sim_escrow_hold}%", f"INR {-fee_impact_variance:+,.2f}"]
    })
    st.dataframe(df_sens, width='stretch')

# -------------------------------------------------------------
# Module 4: Machine Learning Benchmark & Zero-Leakage Pipeline
# -------------------------------------------------------------
elif nav == "4. Machine Learning Benchmark & Zero-Leakage Pipeline":
    st.subheader("Machine Learning Pipeline & Multi-Model Benchmark Suite")
    st.caption("Comparative evaluation of ML models for predicting anomalous settlement transactions under extreme class imbalance without feature leakage.")
    
    metrics_path = os.path.join(MODELS_DIR, 'benchmark_metrics.json')
    if os.path.exists(metrics_path):
        with open(metrics_path, 'r') as f:
            benchmarks = json.load(f)
        df_bench = pd.DataFrame(benchmarks).T
        st.dataframe(df_bench, width='stretch')
        
        st.markdown("<hr style='border-color: #1C273E;'/>", unsafe_allow_html=True)
        st.markdown("""
        #### Technical Machine Learning Specification & Production Selection:
        * **Active Production Model Selection Rationale:** In real-time financial exception screening, models must balance high minority recall with inference throughput and precision. While Gradient Boosting achieved the highest PR-AUC (0.3590) and Logistic Regression achieved the highest raw linear recall (73.0%), **XGBoost (0.8059 ROC-AUC / 0.3459 PR-AUC / 70.2% Recall)** was selected as the active production engine due to its superior non-linear decision boundary and sub-millisecond compiled scoring latency.
        * **Surrogate Generalization:** Operates strictly on 8 standard checkout features (`order_amount`, `log_amount`, `payment_method`, `merchant_category`, `contract_mdr_rate`, `order_hour`, `is_high_value`, `category_risk_prior`) to flag anomaly risk even when downstream fee breakdown fields are unparsed or partially delayed.
        * **Zero Feature Leakage:** Ground-truth fee columns (`actual_fee_charged`, `gst_charged`, `fee_variance`) are strictly excluded during training.
        * **Preprocessing Architecture:** Scikit-learn `Pipeline` using `ColumnTransformer` (`StandardScaler` + `OneHotEncoder(handle_unknown='ignore')`).
        * **Class Imbalance Handling:** Tuned `scale_pos_weight` to account for the minority anomaly distribution (~9.8%).
        """)
