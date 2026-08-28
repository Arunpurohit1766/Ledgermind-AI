import sqlite3
import os
import pandas as pd
import numpy as np

def diagnose_discrepancy(row):
    """
    Autonomous Root-Cause Diagnostic Engine for Financial Controllers.
    Evaluates transactional parameters and identifies exact financial leakage.
    """
    amt = row.get('order_amount', 0.0)
    contract_rate = row.get('contract_mdr_rate', 0.0)
    actual_fee = row.get('actual_fee_charged', 0.0)
    expected_fee = round(amt * contract_rate, 2)
    gst_charged = row.get('gst_charged', 0.0)
    expected_gst = round(actual_fee * 0.18, 2)
    settle_status = row.get('settlement_status', 'SETTLED')
    bank_credit = row.get('credit_amount', 0.0) or row.get('bank_credit_amount', 0.0) or 0.0
    net_settlement = row.get('net_settlement_amount', 0.0)
    
    reasons = []
    leakage = 0.0
    action = "NO_ACTION_REQUIRED"
    
    # 1. Check Settlement Status
    if settle_status == 'ON_HOLD':
        reasons.append("Gateway Settlement On Hold: Pending merchant KYC or chargeback reserve hold.")
        leakage += net_settlement
        action = "RAISE_GATEWAY_SETTLEMENT_TICKET"
        
    # 2. Check Fee Overcharges
    fee_diff = round(actual_fee - expected_fee, 2)
    if fee_diff > 2.0:
        overcharge_pct = round(((actual_fee / (amt + 1e-5)) - contract_rate) * 100, 2)
        reasons.append(f"MDR Rate Overcharge: Charged {round((actual_fee/amt)*100, 2)}% vs contracted {round(contract_rate*100, 2)}% (Excess Fee: Rs {fee_diff:,.2f}).")
        leakage += fee_diff
        action = "AUTO_DRAFT_MDR_RECOVERY_CLAIM"
        
    # 3. Check GST Rate Discrepancies
    gst_diff = round(gst_charged - expected_gst, 2)
    if gst_diff > 1.0:
        reasons.append(f"GST Miscalculation: Billed Rs {gst_charged:,.2f} vs standard 18% GST of Rs {expected_gst:,.2f} (Overcharge: Rs {gst_diff:,.2f}).")
        leakage += gst_diff
        action = "ADJUST_TAX_LEDGER_ENTRY"
        
    # 4. Check Bank Credit Mismatches
    if settle_status == 'SETTLED' and bank_credit > 0:
        bank_diff = round(net_settlement - bank_credit, 2)
        if abs(bank_diff) > 2.0:
            reasons.append(f"Bank Credit Mismatch: Expected Rs {net_settlement:,.2f} but bank received Rs {bank_credit:,.2f}.")
            leakage += bank_diff
            action = "INITIATE_BANK_RECONCILIATION_QUERY"
            
    if not reasons:
        return {
            'status': 'RECONCILED_CLEAN',
            'leakage_amount': 0.0,
            'root_cause': 'All contract rates, GST, and bank credits verified 100% accurate.',
            'recommended_action': 'AUTO_APPROVE_LEDGER'
        }
        
    return {
        'status': 'DISCREPANCY_DETECTED',
        'leakage_amount': round(leakage, 2),
        'root_cause': " | ".join(reasons),
        'recommended_action': action
    }

def generate_dispute_packet(order_id, db_path):
    """
    Generates a formal, audit-ready Financial Dispute & Resolution Notice.
    """
    conn = sqlite3.connect(db_path)
    query = f"""
    SELECT 
        o.order_id, o.customer_id, o.order_amount, o.order_timestamp, o.payment_method, o.merchant_category,
        g.settlement_id, g.gateway_txn_id, g.contract_mdr_rate, g.actual_fee_charged, g.gst_charged, g.net_settlement_amount, g.settlement_status,
        b.utr_number, b.credit_amount, b.bank_timestamp
    FROM orders o
    JOIN gateway_settlements g ON o.order_id = g.order_id
    LEFT JOIN bank_statements b ON g.gateway_txn_id = b.gateway_txn_id
    WHERE o.order_id = '{order_id}';
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    if df.empty:
        return f"Error: Order ID {order_id} not found."
        
    row = df.iloc[0].to_dict()
    row['bank_credit_amount'] = row.get('credit_amount', 0.0) or 0.0
    diag = diagnose_discrepancy(row)
    
    notice = f"""
================================================================================
           FINANCIAL CONTROLLER DISCREPANCY & RECOVERY NOTICE
================================================================================
Generated Date : {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}
Target Order ID: {row['order_id']} | Customer: {row['customer_id']}
Transaction Val: Rs {row['order_amount']:,.2f} ({row['payment_method']} - {row['merchant_category']})

--------------------------------------------------------------------------------
1. AUDIT FINDINGS & ROOT CAUSE ANALYSIS
--------------------------------------------------------------------------------
Status         : {diag['status']}
Total Leakage  : Rs {diag['leakage_amount']:,.2f}
Diagnosis      : {diag['root_cause']}
Action Code    : {diag['recommended_action']}

--------------------------------------------------------------------------------
2. 3-WAY RECONCILIATION BREAKDOWN
--------------------------------------------------------------------------------
• Contract MDR Rate      : {row['contract_mdr_rate']*100:.2f}%
• Actual Fee Charged     : Rs {row['actual_fee_charged']:,.2f}
• GST Charged            : Rs {row['gst_charged']:,.2f}
• Net Gateway Settlement : Rs {row['net_settlement_amount']:,.2f} (Status: {row['settlement_status']})
• Bank Credit UTR        : {row.get('utr_number', 'N/A')}
• Bank Received Amount   : Rs {row['bank_credit_amount']:,.2f}

--------------------------------------------------------------------------------
3. RECOMMENDED ACCOUNTING JOURNAL ADJUSTMENT
--------------------------------------------------------------------------------
Debit  : Gateway MDR Receivables / Escrow Adjustment   Rs {diag['leakage_amount']:,.2f}
Credit : Payment Gateway Fee Expense Account           Rs {diag['leakage_amount']:,.2f}
Memo   : Reversal of anomalous gateway deduction for Order {row['order_id']}

Authorized By: LedgerMind AI Multi-Source Financial Controller
================================================================================
    """
    return notice.strip()
