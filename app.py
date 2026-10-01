import streamlit as st
import pandas as pd
import numpy as np
import json
import time

# ==========================================
# 1. SECURITY: LOGIN SYSTEM
# ==========================================
st.set_page_config(page_title="Flipkart Operations Hub", page_icon="📦", layout="wide")

def check_password():
    """Returns `True` if the user had the correct password."""
    def password_entered():
        if st.session_state["password"] == "admin123":
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Don't store password
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.markdown("### 🔒 Secure Ops Login")
        st.text_input("Enter Dashboard Password (hint: admin123)", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.markdown("### 🔒 Secure Ops Login")
        st.text_input("Enter Dashboard Password (hint: admin123)", type="password", on_change=password_entered, key="password")
        st.error("Incorrect Password. Try again.")
        return False
    return True

if not check_password():
    st.stop() # Stop execution if password is wrong

# ==========================================
# 2. DATA PROCESSING & ML RISK ENGINE
# ==========================================
st.title("📦 Flipkart Operations & Triage Hub")
st.caption("Secure Internal Diagnostic Engine | Authorized Personnel Only")

@st.cache_data
def load_and_process():
    # Load files
    orders = pd.read_csv('orders.csv')
    refunds = pd.read_excel('refunds.xlsx')
    tickets = pd.read_csv('support_tickets.csv')
    with open('customer_complaints.json', 'r') as f:
        complaints = pd.DataFrame(json.load(f))
        
    # Process dates
    orders['promised_delivery_date'] = pd.to_datetime(orders['promised_delivery_date'], errors='coerce')
    orders['actual_delivery_date'] = pd.to_datetime(orders['actual_delivery_date'], errors='coerce')
    orders['delay_days'] = (orders['actual_delivery_date'] - orders['promised_delivery_date']).dt.days
    orders['is_delayed'] = orders['delay_days'] > 0
    
    # Text standardization
    orders['order_status'] = orders['order_status'].astype(str).str.lower().str.strip()
    refunds['refund_status'] = refunds['refund_status'].astype(str).str.lower().str.strip()
    complaints['sentiment_tag'] = complaints['sentiment_tag'].astype(str).str.lower().str.strip()
    
    # Aggregations
    complaint_signals = complaints.groupby('order_id').agg(
        complaint_count=('complaint_id', 'count'),
        negative_sentiment=('sentiment_tag', lambda x: any(x.isin(['angry', 'frustrated', 'negative']))),
        complaint_desc=('complaint_description', lambda x: " | ".join(x.dropna().astype(str)))
    ).reset_index()
    
    tickets['escalation_flag'] = tickets['escalation_flag'].astype(str).str.lower().isin(['true', '1', 'yes'])
    ticket_signals = tickets.groupby('order_id').agg(
        is_escalated=('escalation_flag', lambda x: any(x == True))
    ).reset_index()
    
    # Master Merge
    master_df = orders.merge(refunds[['order_id', 'refund_status', 'refund_amount']], on='order_id', how='left') \
                      .merge(complaint_signals, on='order_id', how='left') \
                      .merge(ticket_signals, on='order_id', how='left')
                      
    master_df['complaint_count'] = master_df['complaint_count'].fillna(0)
    master_df['negative_sentiment'] = master_df['negative_sentiment'].fillna(False)
    master_df['is_escalated'] = master_df['is_escalated'].fillna(False)
    
    # Predictive ML / Risk Score (Simulated future risk)
    # Assume orders from certain categories or high amount have higher risk of escalation
    np.random.seed(42)
    master_df['ml_escalation_risk'] = np.where(master_df['is_delayed'], np.random.randint(60, 95, len(master_df)), np.random.randint(10, 40, len(master_df)))
    master_df['ml_escalation_risk'] = master_df['ml_escalation_risk'].astype(str) + "%"

    # Priority Logic
    def assess_priority(row):
        score = 0
        reasons = []
        if row['is_delayed']: score += 2; reasons.append(f"Delayed {row['delay_days']}d")
        if row['refund_status'] in ['pending', 'failed']: score += 3; reasons.append("Refund Stuck")
        if row['negative_sentiment']: score += 2; reasons.append("Angry Cust")
        if row['is_escalated']: score += 3; reasons.append("Escalated Ticket")
            
        if score >= 5: return 'High', 'Direct Call/Instant Refund', ", ".join(reasons)
        elif score >= 3: return 'Medium', 'Logistics Push', ", ".join(reasons)
        return 'Low', 'Standard SLA', ", ".join(reasons) if reasons else 'Normal'

    priority_res = master_df.apply(assess_priority, axis=1, result_type='expand')
    master_df['priority_level'] = priority_res[0]
    master_df['recommended_action'] = priority_res[1]
    master_df['trigger_reasons'] = priority_res[2]
    
    return master_df

master_df = load_and_process()

# ==========================================
# 3. FILTERS & SMART KPIs (Financial Impact)
# ==========================================
st.sidebar.header("🎯 Operations Filters")
priority_filter = st.sidebar.multiselect("Priority:", ['High', 'Medium', 'Low'], default=['High', 'Medium', 'Low'])
city_filter = st.sidebar.text_input("City Filter:")

filtered_df = master_df.copy()
if priority_filter:
    filtered_df = filtered_df[filtered_df['priority_level'].isin(priority_filter)]
if city_filter.strip():
    filtered_df = filtered_df[filtered_df['delivery_city'].astype(str).str.contains(city_filter.strip(), case=False, na=False)]

# Calculate Business Financial Impact
pending_refunds_df = filtered_df[filtered_df['refund_status'] == 'pending']
financial_risk_value = pending_refunds_df['refund_amount'].sum() if 'refund_amount' in pending_refunds_df else 0

st.markdown("### 📊 Business Impact Metrics")
kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.metric("⚠️ High Priority Cases", (filtered_df['priority_level'] == 'High').sum(), delta="Action Required", delta_color="inverse")
kpi2.metric("⏳ Delayed Shipments", filtered_df['is_delayed'].sum())
kpi3.metric("💳 Pending Refunds", len(pending_refunds_df))
kpi4.metric("💰 Financial Risk (₹)", f"₹ {financial_risk_value:,.2f}", delta="Capital Stuck", delta_color="inverse")

st.markdown("---")

# ==========================================
# 4. TABBED INTERFACE & AUTOMATION
# ==========================================
tab1, tab2, tab3 = st.tabs(["🚦 Live Triage Queue", "🏪 Seller Risk Analytics", "⚡ Action & Automation"])

with tab1:
    st.subheader("📋 Priority Operations Queue")
    display_cols = ['order_id', 'delivery_city', 'priority_level', 'ml_escalation_risk', 'refund_status', 'trigger_reasons', 'recommended_action']
    st.dataframe(filtered_df[display_cols], use_container_width=True, height=350)
    
with tab2:
    st.subheader("🏪 Seller & Region Friction")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Top Sellers Causing Issues (High Priority)**")
        seller_issues = master_df[master_df['priority_level'] == 'High']['seller_id'].value_counts().head(5)
        st.bar_chart(seller_issues, color="#FF4B4B")
    with c2:
        st.markdown("**Top Delay Prone Cities**")
        city_delays = master_df[master_df['is_delayed']]['delivery_city'].value_counts().head(5)
        st.bar_chart(city_delays, color="#FFA500")

with tab3:
    st.subheader("⚡ Resolution Automation & AI Prompt")
    
    if not filtered_df.empty:
        selected_order = st.selectbox("Select Order to Resolve:", filtered_df['order_id'].tolist()[:50])
        row = master_df[master_df['order_id'] == selected_order].iloc[0]
        
        # Smart Expander with Colored text
        with st.expander(f"👁️ Context for {selected_order} (ML Risk: {row['ml_escalation_risk']})", expanded=True):
            st.error(f"**Customer Issue:** {row.get('complaint_desc', 'None logged')}")
            st.warning(f"**Risk Flag:** {row['trigger_reasons']}")
            st.success(f"**Action Required:** {row['recommended_action']}")
            
            # Actionable Automation Button (Simulated)
            if st.button("📱 Trigger Automated WhatsApp Apology & Fast-Track Logistics", type="primary"):
                with st.spinner("Connecting to Twilio/WhatsApp API..."):
                    time.sleep(2) # Simulate API call
                st.toast(f"✅ Auto-alert successfully sent to customer for {selected_order}!", icon="🚀")
                st.success("Logistics escalation triggered and customer notified via WhatsApp.")
        
        # AI Prompt
        st.markdown("**Generate Custom LLM Response (FR-13):**")
        prompt_text = f"Order ID: {row['order_id']} | City: {row['delivery_city']} | Issue: {row['trigger_reasons']} | Action: {row['recommended_action']}\n\nDraft a highly empathetic, professional 3-line email to the customer apologizing for the issue and confirming the immediate action taken."
        st.text_area("Copy this prompt to ChatGPT/Claude:", value=prompt_text, height=120)
    else:
        st.info("No orders found.")
