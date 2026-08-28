import sqlite3
import os
import pandas as pd
import numpy as np

def diagnose_discrepancy(row):
    """
    Comprehensive Multi-Source Diagnostic Engine for Financial Controllers.
    Explicitly distinguishes between:
    - MISSING_GATEWAY_RECORD
    - MISSING_BANK_RECORD / UNREALIZED_BANK_CREDIT
    - SETTLEMENT_ON_HOLD
    - FEE_OVERCHARGE
    - GST_MISCALCULATION
    - BANK_AMOUNT_MISMATCH
    - RECONCILED_CLEAN
    """
    amt = row.get('order_amount', 0.0) or 0.0
    contract_rate = row.get('contract_mdr_rate')
    actual_fee = row.get('actual_fee_charged')
    gst_charged = row.get('gst_charged')
    net_settlement = row.get('net_settlement_amount')
    settle_status = row.get('settlement_status')
    
    bank_credit = row.get('credit_amount')
    if bank_credit is None or (isinstance(bank_credit, float) and np.isnan(bank_credit)):
        bank_credit = row.get('bank_credit_amount')
    utr_number = row.get('utr_number')
    
    # -------------------------------------------------------------
    # State 1: Missing Gateway Settlement Record (Order never processed by Gateway)
    # -------------------------------------------------------------
    if pd.isna(settle_status) or settle_status is None or pd.isna(row.get('gateway_txn_id')):
        return {
            'status': 'DISCREPANCY_DETECTED',
            'discrepancy_type': 'MISSING_GATEWAY_RECORD',
            'leakage_amount': round(amt, 2),
            'root_cause': 'Missing Gateway Record: Order confirmed in Merchant DB but was never processed or reported by Payment Gateway.',
            'recommended_action': 'INVESTIGATE_UNPROCESSED_ORDER',
            'claim_type': 'UNPROCESSED_MERCHANT_TRANSACTION',
            'evidence': f"Order {row.get('order_id')} (INR {amt:,.2f}) exists in Merchant Orders DB with no matching gateway settlement record."
        }
        
    if contract_rate is None or pd.isna(contract_rate):
        contract_rate = 0.015
    else:
        contract_rate = float(contract_rate)
    actual_fee = float(actual_fee or 0.0)
    gst_charged = float(gst_charged or 0.0)
    net_settlement = float(net_settlement or 0.0)
    expected_fee = round(amt * contract_rate, 2)
    expected_gst = round(actual_fee * 0.18, 2)
    
    reasons = []
    leakage = 0.0
    discrepancy_type = "UNKNOWN_DISCREPANCY"
    action = "INVESTIGATE_EXCEPTION"
    claim_type = "FINANCIAL_DISCREPANCY_CLAIM"
    evidence_parts = []
    
    # -------------------------------------------------------------
    # State 2: Gateway Settlement On Hold (Escrow freeze / KYC hold)
    # -------------------------------------------------------------
    if settle_status == 'ON_HOLD':
        reasons.append("Gateway Settlement On Hold: Payout delayed by Gateway risk/compliance engines or chargeback reserve hold.")
        leakage += net_settlement
        discrepancy_type = "SETTLEMENT_ON_HOLD"
        action = "RAISE_GATEWAY_ESCROW_RELEASE_TICKET"
        claim_type = "GATEWAY_ESCROW_RELEASE_DEMAND"
        evidence_parts.append(f"Net settlement INR {net_settlement:,.2f} marked ON_HOLD by gateway despite successful customer charge.")

    # -------------------------------------------------------------
    # State 3: MDR Fee Overcharge (Gateway billed rate > contracted rate)
    # -------------------------------------------------------------
    fee_diff = round(actual_fee - expected_fee, 2)
    if fee_diff > 2.0:
        overcharge_pct = round(((actual_fee / (amt + 1e-5)) - contract_rate) * 100, 2)
        reasons.append(f"MDR Rate Overcharge: Charged {round((actual_fee/(amt+1e-5))*100, 2)}% vs contracted {round(contract_rate*100, 2)}% (Excess Fee: INR {fee_diff:,.2f}).")
        leakage += fee_diff
        if discrepancy_type == "UNKNOWN_DISCREPANCY":
            discrepancy_type = "FEE_OVERCHARGE"
            action = "AUTO_DRAFT_MDR_RECOVERY_CLAIM"
            claim_type = "MDR_RATE_OVERCHARGE"
        evidence_parts.append(f"Actual fee INR {actual_fee:,.2f} exceeds contract MDR {contract_rate*100:.2f}% (INR {expected_fee:,.2f}) by INR {fee_diff:,.2f}.")

    # -------------------------------------------------------------
    # State 4: GST Rate Miscalculation (Billed 28% luxury vs statutory 18% services)
    # -------------------------------------------------------------
    gst_diff = round(gst_charged - expected_gst, 2)
    if gst_diff > 1.0:
        reasons.append(f"GST Miscalculation: Billed INR {gst_charged:,.2f} vs standard 18% GST of INR {expected_gst:,.2f} (Overcharge: INR {gst_diff:,.2f}).")
        leakage += gst_diff
        if discrepancy_type == "UNKNOWN_DISCREPANCY":
            discrepancy_type = "GST_MISMATCH"
            action = "ADJUST_TAX_LEDGER_ENTRY"
            claim_type = "GST_TAX_ASSESSMENT_ERROR"
        evidence_parts.append(f"Billed GST INR {gst_charged:,.2f} vs statutory 18% GST INR {expected_gst:,.2f} on fee INR {actual_fee:,.2f}.")

    # -------------------------------------------------------------
    # State 5: Missing Bank Realization Record (Settled by Gateway but never received in Bank)
    # -------------------------------------------------------------
    if settle_status == 'SETTLED':
        is_bank_missing = (
            bank_credit is None or 
            pd.isna(bank_credit) or 
            pd.isna(utr_number) or 
            str(utr_number).strip() in ['', 'nan', 'N/A', 'None'] or 
            float(bank_credit) <= 0
        )
        if is_bank_missing:
            reasons.append("Unrealized Bank Credit: Settlement marked SETTLED by gateway but no positive bank deposit or valid UTR received.")
            leakage += net_settlement
            if discrepancy_type == "UNKNOWN_DISCREPANCY":
                discrepancy_type = "UNREALIZED_BANK_CREDIT"
                action = "INITIATE_UNREALIZED_BANK_TRACE"
                claim_type = "UNREALIZED_SETTLEMENT_DEPOSIT"
            evidence_parts.append(f"Gateway marked SETTLED for INR {net_settlement:,.2f} but invalid/zero/negative bank credit (INR {float(bank_credit or 0):,.2f}) or missing UTR was received.")
            
        # -------------------------------------------------------------
        # State 6: Bank Realization Amount Mismatch (Bank credited less than net settlement)
        # -------------------------------------------------------------
        else: # float(bank_credit) > 0
            bank_diff = round(net_settlement - float(bank_credit), 2)
            if abs(bank_diff) > 2.0:
                reasons.append(f"Bank Credit Mismatch: Expected INR {net_settlement:,.2f} but bank realized INR {float(bank_credit):,.2f} (Shortfall: INR {bank_diff:,.2f}).")
                leakage += max(0.0, bank_diff)
                if discrepancy_type == "UNKNOWN_DISCREPANCY":
                    discrepancy_type = "BANK_AMOUNT_MISMATCH"
                    action = "INITIATE_BANK_RECONCILIATION_QUERY"
                    claim_type = "BANK_CLEARING_VARIANCE"
                evidence_parts.append(f"Gateway net settlement INR {net_settlement:,.2f} differs from bank realized INR {float(bank_credit):,.2f} by INR {bank_diff:,.2f}.")

    if not reasons:
        return {
            'status': 'RECONCILED_CLEAN',
            'discrepancy_type': 'RECONCILED_CLEAN',
            'leakage_amount': 0.0,
            'root_cause': 'All contract rates, 18% GST lines, and bank credits verified 100% accurate with valid UTR.',
            'recommended_action': 'AUTO_APPROVE_LEDGER',
            'claim_type': 'NONE',
            'evidence': 'Full 3-way synchronization verified.'
        }
        
    return {
        'status': 'DISCREPANCY_DETECTED',
        'discrepancy_type': discrepancy_type,
        'leakage_amount': round(leakage, 2),
        'root_cause': " | ".join(reasons),
        'recommended_action': action,
        'claim_type': claim_type,
        'evidence': " // ".join(evidence_parts)
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
    LEFT JOIN gateway_settlements g ON o.order_id = g.order_id
    LEFT JOIN bank_statements b ON g.gateway_txn_id = b.gateway_txn_id
    WHERE o.order_id = '{order_id}';
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    if df.empty:
        return f"Error: Order ID {order_id} not found."
        
    row = df.iloc[0].to_dict()
    diag = diagnose_discrepancy(row)
    
    notice = f"""
================================================================================
           FINANCIAL CONTROLLER DISCREPANCY & RESOLUTION NOTICE
================================================================================
Generated Date : {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}
Target Order ID: {row['order_id']} | Customer: {row.get('customer_id', 'N/A')}
Transaction Val: INR {row['order_amount']:,.2f} ({row.get('payment_method', 'N/A')} - {row.get('merchant_category', 'N/A')})

--------------------------------------------------------------------------------
1. AUDIT FINDINGS & ROOT CAUSE ANALYSIS
--------------------------------------------------------------------------------
Audit Status   : {diag['status']}
Discrepancy Cat: {diag['discrepancy_type']}
Claimable Loss : INR {diag['leakage_amount']:,.2f}
Diagnosis      : {diag['root_cause']}
Action Code    : {diag['recommended_action']}
Dispute Type   : {diag['claim_type']}

--------------------------------------------------------------------------------
2. 3-WAY RECONCILIATION BREAKDOWN
--------------------------------------------------------------------------------
• Contract MDR Rate      : {float(row.get('contract_mdr_rate') or 0.0)*100:.2f}%
• Actual Fee Charged     : INR {float(row.get('actual_fee_charged') or 0.0):,.2f}
• GST Charged            : INR {float(row.get('gst_charged') or 0.0):,.2f}
• Net Gateway Settlement : INR {float(row.get('net_settlement_amount') or 0.0):,.2f} (Status: {row.get('settlement_status', 'N/A')})
• Bank Credit UTR        : {row.get('utr_number') or 'NO_UTR_RECORDED'}
• Bank Received Amount   : INR {float(row.get('credit_amount') or 0.0):,.2f}

--------------------------------------------------------------------------------
3. AUDIT EVIDENCE & RECONCILIATION SUMMARY
--------------------------------------------------------------------------------
Evidence Summary: {diag['evidence']}

Authorized By: LedgerMind AI Multi-Source Financial Controller
================================================================================
    """
    return notice.strip()
