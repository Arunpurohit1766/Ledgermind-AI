import sqlite3
import os
import pandas as pd
import numpy as np

def diagnose_discrepancy(row):
    """
    Canonical Single Source of Truth Diagnostic Engine for Multi-Source Financial Reconciliation.
    Evaluates transactional parameters across Orders, Gateway Settlements, and Bank Statements.
    Guarantees strict pre-calculation financial validation and exact-paisa component allocation.
    """
    # -------------------------------------------------------------
    # 1. Strict Validation Boundary: Order Amount
    # -------------------------------------------------------------
    raw_amt = row.get('order_amount')
    if raw_amt is None or pd.isna(raw_amt):
        return {
            'status': 'DISCREPANCY_DETECTED',
            'discrepancy_type': 'INVALID_FINANCIAL_DATA',
            'leakage_amount': 0.0,
            'fee_variance': 0.0,
            'tax_variance': 0.0,
            'bank_variance': 0.0,
            'root_cause': 'Invalid Order Amount: Missing or null transaction value.',
            'recommended_action': 'REJECT_INVALID_RECORD',
            'claim_type': 'DATA_VALIDATION_ERROR',
            'evidence': f"Order {row.get('order_id', 'UNKNOWN')} has null order amount."
        }
        
    try:
        amt = float(raw_amt)
        if np.isnan(amt) or np.isinf(amt) or amt <= 0:
            raise ValueError()
    except (ValueError, TypeError):
        return {
            'status': 'DISCREPANCY_DETECTED',
            'discrepancy_type': 'INVALID_FINANCIAL_DATA',
            'leakage_amount': 0.0,
            'fee_variance': 0.0,
            'tax_variance': 0.0,
            'bank_variance': 0.0,
            'root_cause': f'Invalid Order Amount: Non-numeric, non-positive, or infinite value ({raw_amt}).',
            'recommended_action': 'REJECT_INVALID_RECORD',
            'claim_type': 'DATA_VALIDATION_ERROR',
            'evidence': f"Order {row.get('order_id', 'UNKNOWN')} amount '{raw_amt}' failed numeric validation."
        }
        
    raw_settle_status = row.get('settlement_status')
    gateway_txn_id = row.get('gateway_txn_id')
    
    # -------------------------------------------------------------
    # 2. State: Missing Gateway Settlement Record
    # -------------------------------------------------------------
    if (pd.isna(raw_settle_status) or raw_settle_status is None or 
        pd.isna(gateway_txn_id) or str(gateway_txn_id).strip() in ['', 'nan', 'None', 'N/A']):
        return {
            'status': 'DISCREPANCY_DETECTED',
            'discrepancy_type': 'MISSING_GATEWAY_RECORD',
            'leakage_amount': round(amt, 2),
            'fee_variance': 0.0,
            'tax_variance': 0.0,
            'bank_variance': 0.0,
            'root_cause': 'Missing Gateway Record: Order confirmed in Merchant DB but was never processed or reported by Payment Gateway.',
            'recommended_action': 'INVESTIGATE_UNPROCESSED_ORDER',
            'claim_type': 'UNPROCESSED_MERCHANT_TRANSACTION',
            'evidence': f"Order {row.get('order_id')} (INR {amt:,.2f}) exists in Merchant Orders DB with no matching gateway settlement record."
        }
        
    settle_status = str(raw_settle_status).strip().upper()
    if settle_status not in ['SETTLED', 'ON_HOLD']:
        return {
            'status': 'DISCREPANCY_DETECTED',
            'discrepancy_type': 'INVALID_SETTLEMENT_STATUS',
            'leakage_amount': round(amt, 2),
            'fee_variance': 0.0,
            'tax_variance': 0.0,
            'bank_variance': 0.0,
            'root_cause': f"Unknown Settlement Status '{raw_settle_status}'. Gateway records must be SETTLED or ON_HOLD.",
            'recommended_action': 'AUDIT_UNKNOWN_GATEWAY_STATUS',
            'claim_type': 'STATUS_NORMALIZATION_ERROR',
            'evidence': f"Order {row.get('order_id')} contains non-standard settlement status '{raw_settle_status}'."
        }
        
    # -------------------------------------------------------------
    # 3. Strict Pre-Calculation Validation of Gateway Financial Numbers
    # -------------------------------------------------------------
    contract_rate_raw = row.get('contract_mdr_rate')
    actual_fee_raw = row.get('actual_fee_charged')
    gst_charged_raw = row.get('gst_charged')
    net_settlement_raw = row.get('net_settlement_amount')
    
    for field_name, field_val in [
        ('contract_mdr_rate', contract_rate_raw),
        ('actual_fee_charged', actual_fee_raw),
        ('gst_charged', gst_charged_raw),
        ('net_settlement_amount', net_settlement_raw)
    ]:
        if field_val is None or pd.isna(field_val):
            return {
                'status': 'DISCREPANCY_DETECTED',
                'discrepancy_type': 'INVALID_GATEWAY_FINANCIAL_DATA',
                'leakage_amount': round(amt, 2),
                'fee_variance': 0.0,
                'tax_variance': 0.0,
                'bank_variance': 0.0,
                'root_cause': f"Malformed Gateway Data: Required field '{field_name}' is missing or null.",
                'recommended_action': 'REJECT_MALFORMED_SETTLEMENT_RECORD',
                'claim_type': 'INVALID_SETTLEMENT_DATA',
                'evidence': f"Order {row.get('order_id')} has null '{field_name}' in gateway feed."
            }
        try:
            val_f = float(field_val)
            if np.isnan(val_f) or np.isinf(val_f) or val_f < 0:
                raise ValueError()
        except (ValueError, TypeError):
            return {
                'status': 'DISCREPANCY_DETECTED',
                'discrepancy_type': 'INVALID_GATEWAY_FINANCIAL_DATA',
                'leakage_amount': round(amt, 2),
                'fee_variance': 0.0,
                'tax_variance': 0.0,
                'bank_variance': 0.0,
                'root_cause': f"Malformed Gateway Data: Field '{field_name}' ({field_val}) is negative, non-numeric, or infinite.",
                'recommended_action': 'REJECT_MALFORMED_SETTLEMENT_RECORD',
                'claim_type': 'INVALID_SETTLEMENT_DATA',
                'evidence': f"Order {row.get('order_id')} contains invalid numeric value '{field_val}' for '{field_name}'."
            }

    contract_rate = float(contract_rate_raw)
    actual_fee = float(actual_fee_raw)
    gst_charged = float(gst_charged_raw)
    net_settlement = float(net_settlement_raw)
    expected_fee = round(amt * contract_rate, 2)
    expected_gst = round(actual_fee * 0.18, 2)
    
    bank_credit = row.get('credit_amount')
    if bank_credit is None or (isinstance(bank_credit, float) and np.isnan(bank_credit)):
        bank_credit = row.get('bank_credit_amount')
    utr_number = row.get('utr_number')
    clearing_status = str(row.get('clearing_status') or 'CLEARED').strip().upper()
    
    reasons = []
    discrepancy_type = "UNKNOWN_DISCREPANCY"
    action = "INVESTIGATE_EXCEPTION"
    claim_type = "FINANCIAL_DISCREPANCY_CLAIM"
    evidence_parts = []
    
    f_leak = 0.0
    t_leak = 0.0
    b_leak = 0.0
    
    # -------------------------------------------------------------
    # 4. State: Gateway Settlement On Hold
    # -------------------------------------------------------------
    if settle_status == 'ON_HOLD':
        reasons.append("Gateway Settlement On Hold: Payout delayed by Gateway risk/compliance engines or chargeback reserve hold.")
        discrepancy_type = "SETTLEMENT_ON_HOLD"
        action = "RAISE_GATEWAY_ESCROW_RELEASE_TICKET"
        claim_type = "GATEWAY_ESCROW_RELEASE_DEMAND"
        evidence_parts.append(f"Net settlement INR {net_settlement:,.2f} marked ON_HOLD by gateway despite successful customer charge.")

    # -------------------------------------------------------------
    # 5. State: MDR Fee Overcharge / Undercharge
    # -------------------------------------------------------------
    fee_diff = round(actual_fee - expected_fee, 2)
    if fee_diff > 2.0:
        overcharge_pct = round(((actual_fee / (amt + 1e-5)) - contract_rate) * 100, 2)
        reasons.append(f"MDR Rate Overcharge: Charged {round((actual_fee/(amt+1e-5))*100, 2)}% vs contracted {round(contract_rate*100, 2)}% (Excess Fee: INR {fee_diff:,.2f}).")
        f_leak = fee_diff
        if discrepancy_type == "UNKNOWN_DISCREPANCY":
            discrepancy_type = "FEE_OVERCHARGE"
            action = "AUTO_DRAFT_MDR_RECOVERY_CLAIM"
            claim_type = "MDR_RATE_OVERCHARGE"
        evidence_parts.append(f"Actual fee INR {actual_fee:,.2f} exceeds contract MDR {contract_rate*100:.2f}% (INR {expected_fee:,.2f}) by INR {fee_diff:,.2f}.")
    elif fee_diff < -2.0:
        undercharge_amt = abs(fee_diff)
        reasons.append(f"MDR Fee Undercharge (Favorable): Billed INR {actual_fee:,.2f} vs contracted INR {expected_fee:,.2f} (Undercharged by INR {undercharge_amt:,.2f}).")
        if discrepancy_type == "UNKNOWN_DISCREPANCY":
            discrepancy_type = "FEE_UNDERCHARGE"
            action = "LOG_FAVORABLE_VARIANCE"
            claim_type = "FAVORABLE_MDR_VARIANCE"
        evidence_parts.append(f"Actual fee INR {actual_fee:,.2f} is lower than contracted MDR {contract_rate*100:.2f}% by INR {undercharge_amt:,.2f}.")

    # -------------------------------------------------------------
    # 6. State: GST Rate Miscalculation
    # -------------------------------------------------------------
    gst_diff = round(gst_charged - expected_gst, 2)
    if gst_diff > 1.0:
        reasons.append(f"GST Miscalculation: Billed INR {gst_charged:,.2f} vs configured 18% GST benchmark of INR {expected_gst:,.2f} (Overcharge: INR {gst_diff:,.2f}).")
        t_leak = gst_diff
        if discrepancy_type == "UNKNOWN_DISCREPANCY":
            discrepancy_type = "GST_MISMATCH"
            action = "ADJUST_TAX_LEDGER_ENTRY"
            claim_type = "GST_TAX_ASSESSMENT_ERROR"
        evidence_parts.append(f"Billed GST INR {gst_charged:,.2f} vs configured 18% GST benchmark INR {expected_gst:,.2f} on fee INR {actual_fee:,.2f}.")
    elif gst_diff < -1.0:
        tax_undercharge = abs(gst_diff)
        reasons.append(f"GST Undercharge (Favorable): Billed INR {gst_charged:,.2f} vs benchmark INR {expected_gst:,.2f}.")
        if discrepancy_type == "UNKNOWN_DISCREPANCY":
            discrepancy_type = "GST_MISMATCH"
            action = "LOG_FAVORABLE_TAX_VARIANCE"
            claim_type = "FAVORABLE_TAX_VARIANCE"

    # -------------------------------------------------------------
    # 7. State: Missing, Non-Positive, or Uncleared Bank Realization Record
    # -------------------------------------------------------------
    if settle_status == 'SETTLED':
        is_bank_missing = (
            bank_credit is None or 
            pd.isna(bank_credit) or 
            pd.isna(utr_number) or 
            str(utr_number).strip() in ['', 'nan', 'N/A', 'None'] or 
            float(bank_credit) <= 0 or
            clearing_status != 'CLEARED'
        )
        if is_bank_missing:
            reasons.append("Unrealized Bank Credit: Settlement marked SETTLED by gateway but no cleared positive bank deposit or valid UTR received.")
            if discrepancy_type == "UNKNOWN_DISCREPANCY":
                discrepancy_type = "UNREALIZED_BANK_CREDIT"
                action = "INITIATE_UNREALIZED_BANK_TRACE"
                claim_type = "UNREALIZED_SETTLEMENT_DEPOSIT"
            evidence_parts.append(f"Gateway marked SETTLED for INR {net_settlement:,.2f} but bank record is invalid, uncleared ({clearing_status}), zero, or missing UTR.")
            
        # -------------------------------------------------------------
        # 8. State: Bank Realization Shortfall / Over-Credit
        # -------------------------------------------------------------
        else:
            bank_diff = round(net_settlement - float(bank_credit), 2)
            if bank_diff > 2.0:
                reasons.append(f"Bank Credit Mismatch: Expected INR {net_settlement:,.2f} but bank realized INR {float(bank_credit):,.2f} (Shortfall: INR {bank_diff:,.2f}).")
                b_leak = bank_diff
                if discrepancy_type == "UNKNOWN_DISCREPANCY":
                    discrepancy_type = "BANK_AMOUNT_MISMATCH"
                    action = "INITIATE_BANK_RECONCILIATION_QUERY"
                    claim_type = "BANK_CLEARING_VARIANCE"
                evidence_parts.append(f"Gateway net settlement INR {net_settlement:,.2f} differs from bank realized INR {float(bank_credit):,.2f} by INR {bank_diff:,.2f}.")
            elif bank_diff < -2.0:
                over_credit = abs(bank_diff)
                reasons.append(f"Bank Realization Over-Credit (Favorable): Expected INR {net_settlement:,.2f} but bank realized INR {float(bank_credit):,.2f} (Favorable variance: INR {over_credit:,.2f}).")
                if discrepancy_type == "UNKNOWN_DISCREPANCY":
                    discrepancy_type = "BANK_AMOUNT_MISMATCH"
                    action = "LOG_FAVORABLE_BANK_VARIANCE"
                    claim_type = "FAVORABLE_BANK_VARIANCE"

    # -------------------------------------------------------------
    # 9. Exact Canonical Paisa Leakage Calculation
    # -------------------------------------------------------------
    if not reasons:
        return {
            'status': 'RECONCILED_CLEAN',
            'discrepancy_type': 'RECONCILED_CLEAN',
            'leakage_amount': 0.0,
            'fee_variance': 0.0,
            'tax_variance': 0.0,
            'bank_variance': 0.0,
            'root_cause': 'All reconciliation variances are within configured tolerances and the settlement has a valid bank realization.',
            'recommended_action': 'MARK_RECONCILED',
            'claim_type': 'NONE',
            'evidence': 'Full 3-way synchronization verified.'
        }
        
    if discrepancy_type == 'SETTLEMENT_ON_HOLD':
        total_leakage = round(net_settlement + f_leak + t_leak, 2)
    elif discrepancy_type == 'UNREALIZED_BANK_CREDIT':
        total_leakage = round(net_settlement + f_leak + t_leak, 2)
    elif discrepancy_type == 'FEE_UNDERCHARGE':
        total_leakage = 0.0
    else:
        total_leakage = round(f_leak + t_leak + b_leak, 2)
        
    return {
        'status': 'DISCREPANCY_DETECTED',
        'discrepancy_type': discrepancy_type,
        'leakage_amount': total_leakage,
        'fee_variance': round(f_leak, 2),
        'tax_variance': round(t_leak, 2),
        'bank_variance': round(b_leak, 2),
        'root_cause': " | ".join(reasons),
        'recommended_action': action,
        'claim_type': claim_type,
        'evidence': " // ".join(evidence_parts)
    }

def generate_dispute_packet(order_id, db_path):
    """
    Generates a formal, audit-ready Financial Dispute & Resolution Notice.
    Uses parameterized SQL to guarantee injection safety.
    """
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    query = """
    SELECT 
        o.order_id, o.customer_id, o.order_amount, o.order_timestamp, o.payment_method, o.merchant_category,
        g.settlement_id, g.gateway_txn_id, g.contract_mdr_rate, g.actual_fee_charged, g.gst_charged, g.net_settlement_amount, g.settlement_status,
        b.utr_number, b.credit_amount, b.bank_timestamp, b.clearing_status
    FROM orders o
    LEFT JOIN gateway_settlements g ON o.order_id = g.order_id
    LEFT JOIN bank_statements b ON g.gateway_txn_id = b.gateway_txn_id
    WHERE o.order_id = ?;
    """
    df = pd.read_sql_query(query, conn, params=(order_id,))
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
• Bank Received Amount   : INR {float(row.get('credit_amount') or 0.0):,.2f} (Status: {row.get('clearing_status', 'N/A')})

--------------------------------------------------------------------------------
3. AUDIT EVIDENCE & RECONCILIATION SUMMARY
--------------------------------------------------------------------------------
Evidence Summary: {diag['evidence']}

Prepared by LedgerMind AI for Finance Review
================================================================================
    """
    return notice.strip()
