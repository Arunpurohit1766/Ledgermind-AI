import sqlite3
import numpy as np
import pandas as pd
import os
from datetime import datetime, timedelta

def initialize_database(db_path, n_records=50000, random_state=42):
    np.random.seed(random_state)
    if os.path.exists(db_path):
        os.remove(db_path)
    conn = sqlite3.connect(db_path)
    conn.execute('PRAGMA foreign_keys = ON;')
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS orders (
        order_id TEXT PRIMARY KEY,
        customer_id TEXT,
        order_amount REAL,
        order_timestamp TEXT,
        payment_method TEXT,
        merchant_category TEXT,
        order_status TEXT
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS gateway_settlements (
        settlement_id TEXT PRIMARY KEY,
        order_id TEXT,
        gateway_txn_id TEXT UNIQUE,
        gross_amount REAL,
        contract_mdr_rate REAL,
        actual_fee_charged REAL,
        gst_charged REAL,
        net_settlement_amount REAL,
        settlement_status TEXT,
        settlement_timestamp TEXT,
        FOREIGN KEY (order_id) REFERENCES orders(order_id)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS bank_statements (
        bank_txn_id TEXT PRIMARY KEY,
        gateway_txn_id TEXT,
        utr_number TEXT UNIQUE,
        credit_amount REAL,
        bank_timestamp TEXT,
        clearing_status TEXT
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS audit_ledger (
        audit_id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id TEXT,
        anomaly_type TEXT,
        leakage_amount REAL,
        ai_confidence REAL,
        root_cause_explanation TEXT,
        action_taken TEXT,
        timestamp TEXT
    )
    ''')
    
    base_date = datetime(2026, 1, 1, 9, 0, 0)
    order_ids = [f"ORD-{100000 + i}" for i in range(n_records)]
    customer_ids = [f"CUST-{np.random.randint(10000, 99999)}" for _ in range(n_records)]
    
    payment_methods = ['UPI', 'Credit Card', 'Debit Card', 'Net Banking']
    methods = np.random.choice(payment_methods, size=n_records, p=[0.50, 0.25, 0.15, 0.10])
    
    categories = ['Retail', 'SaaS', 'Travel', 'Gaming', 'Electronics', 'Utilities']
    cats = np.random.choice(categories, size=n_records, p=[0.30, 0.20, 0.15, 0.10, 0.15, 0.10])
    
    amounts = np.round(np.random.exponential(scale=3500, size=n_records) + 150, 2)
    seconds_offset = np.random.randint(0, 60 * 24 * 3600, size=n_records)
    timestamps = [(base_date + timedelta(seconds=int(s))).strftime('%Y-%m-%d %H:%M:%S') for s in seconds_offset]
    
    contract_rates = {'UPI': 0.000, 'Debit Card': 0.009, 'Credit Card': 0.019, 'Net Banking': 0.015}
    category_risk_prior = {'Gaming': 0.8, 'Travel': 0.7, 'Electronics': 0.5, 'SaaS': 0.3, 'Retail': 0.2, 'Utilities': 0.1}
    
    order_data = []
    gateway_data = []
    bank_data = []
    
    for i in range(n_records):
        oid = order_ids[i]
        cid = customer_ids[i]
        amt = amounts[i]
        pm = methods[i]
        cat = cats[i]
        ts_order = timestamps[i]
        dt_order = datetime.strptime(ts_order, '%Y-%m-%d %H:%M:%S')
        order_hour = dt_order.hour
        
        status = 'SUCCESS'
        if np.random.rand() < 0.02:
            status = 'FAILED'
        elif np.random.rand() < 0.01:
            status = 'REFUNDED'
            
        order_data.append((oid, cid, amt, ts_order, pm, cat, status))
        if status != 'SUCCESS':
            continue
            
        gtxn_id = f"GZ-{200000 + i}"
        sid = f"SETTLE-{300000 + i}"
        contract_rate = contract_rates[pm]
        expected_fee = np.round(amt * contract_rate, 2)
        
        risk_score = -4.2
        if category_risk_prior.get(cat, 0.2) >= 0.5:
            risk_score += 1.8
        if pm in ['Credit Card', 'Net Banking']:
            risk_score += 1.3
        if amt > 12000:
            risk_score += 1.6
        if 18 <= order_hour <= 23 or 11 <= order_hour <= 14:
            risk_score += 0.8
            
        prob_anomaly = 1.0 / (1.0 + np.exp(-risk_score))
        rand_val = np.random.rand()
        anomaly = 'NONE'
        
        if rand_val < prob_anomaly:
            sub_type = np.random.rand()
            if sub_type < 0.45:
                anomaly = 'FEE_OVERCHARGE'
                fee_surcharge = min(amt * 0.08, (amt * 0.015) + np.random.uniform(25, 95))
                actual_fee = np.round(min(amt * 0.40, expected_fee + fee_surcharge), 2)
                gst = np.round(actual_fee * 0.18, 2)
            elif sub_type < 0.75:
                anomaly = 'GST_MISCALCULATION'
                actual_fee = expected_fee
                gst = np.round(actual_fee * 0.28, 2)
            else:
                anomaly = 'UNSETTLED_HOLD'
                actual_fee = expected_fee
                gst = np.round(actual_fee * 0.18, 2)
        else:
            actual_fee = expected_fee
            gst = np.round(actual_fee * 0.18, 2)
            
        net_settlement = np.round(max(0.0, amt - actual_fee - gst), 2)
        settle_status = 'ON_HOLD' if anomaly == 'UNSETTLED_HOLD' else 'SETTLED'
        ts_settle = (dt_order + timedelta(hours=int(np.random.randint(12, 36)))).strftime('%Y-%m-%d %H:%M:%S')
        gateway_data.append((sid, oid, gtxn_id, amt, contract_rate, actual_fee, gst, net_settlement, settle_status, ts_settle))
        
        if settle_status == 'SETTLED':
            btxn_id = f"BNK-{400000 + i}"
            utr = f"UTR{7000000000 + i}"
            ts_bank = (datetime.strptime(ts_settle, '%Y-%m-%d %H:%M:%S') + timedelta(hours=int(np.random.randint(4, 24)))).strftime('%Y-%m-%d %H:%M:%S')
            
            if np.random.rand() < 0.015:
                credit_amt = np.round(max(0.0, net_settlement - min(net_settlement * 0.2, np.random.uniform(25.0, 180.0))), 2)
            else:
                credit_amt = net_settlement
                
            bank_status = 'CLEARED'
            bank_data.append((btxn_id, gtxn_id, utr, credit_amt, ts_bank, bank_status))
            
    cursor.executemany('INSERT INTO orders VALUES (?, ?, ?, ?, ?, ?, ?)', order_data)
    cursor.executemany('INSERT INTO gateway_settlements VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', gateway_data)
    cursor.executemany('INSERT INTO bank_statements VALUES (?, ?, ?, ?, ?, ?)', bank_data)
    conn.commit()
    conn.close()

if __name__ == '__main__':
    project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_file = os.path.join(project_dir, 'data', 'financial_ledger.db')
    initialize_database(db_file, n_records=50000)
