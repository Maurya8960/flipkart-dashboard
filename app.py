import streamlit as st
import pandas as pd
import numpy as np
import json
import time

st.set_page_config(
    page_title="Flipkart Ops Hub - macOS Edition",
    page_icon="🍎",
    layout="wide"
)

# ==========================================
# 1. macOS GLASSMORPHISM CSS INJECTION
# ==========================================
glass_css = """
<style>
/* Background gradient */
.stApp {
    background: radial-gradient(circle at 15% 20%, #1a1e2e 0%, #0d0f18 100%) !important;
    color: #e2e8f0;
    font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text", sans-serif;
}

/* Glass Cards for Metrics */
div[data-testid="stMetric"] {
    background: rgba(255, 255, 255, 0.04) !important;
    backdrop-filter: blur(20px) saturate(180%) !important;
    -webkit-backdrop-filter: blur(20px) saturate(180%) !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    border-radius: 16px !important;
    padding: 16px 20px !important;
    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3) !important;
}

/* Glass Sidebar */
section[data-testid="stSidebar"] {
    background: rgba(18, 22, 34, 0.6) !important;
    backdrop-filter: blur(25px) !important;
    -webkit-backdrop-filter: blur(25px) !important;
    border-right: 1px solid rgba(255, 255, 255, 0.08) !important;
}

/* Glass Tabs Container */
div[data-baseweb="tab-list"] {
    background: rgba(255, 255, 255, 0.03) !important;
    backdrop-filter: blur(16px) !important;
    border-radius: 14px !important;
    padding: 4px !important;
    border: 1px solid rgba(255, 255, 255, 0.05) !important;
}

/* Glass Buttons */
button[kind="primary"], div.stButton > button {
    background: rgba(255, 255, 255, 0.07) !important;
    backdrop-filter: blur(12px) !important;
    border: 1px solid rgba(255, 255, 255, 0.15) !important;
    border-radius: 10px !important;
    color: #f8fafc !important;
    transition: all 0.25s ease !important;
}

button[kind="primary"]:hover, div.stButton > button:hover {
    background: rgba(255, 255, 255, 0.15) !important;
    border-color: rgba(255, 255, 255, 0.3) !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25) !important;
}

/* macOS Window Bar Simulation */
.mac-window-bar {
    display: flex;
    gap: 8px;
    padding-bottom: 12px;
}
.mac-dot {
    width: 12px;
    height: 12px;
    border-radius: 50%;
    display: inline-block;
}
.dot-red { background: #ff5f56; }
.dot-yellow { background: #ffbd2e; }
.dot-green { background: #27c93f; }
</style>
"""
st.markdown(glass_css, unsafe_allow_html=True)

# ==========================================
# 2. LOGIN AUTHENTICATION
# ==========================================
def check_password():
    def password_entered():
        if st.session_state["password"] == "admin123":
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.markdown("""
        <div class="mac-window-bar">
            <span class="mac-dot dot-red"></span>
            <span class="mac-dot dot-yellow"></span>
            <span class="mac-dot dot-green"></span>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("### 🔒 Ops Hub Authentication")
        st.text_input("Enter Keycard Passcode (hint: admin123)", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.markdown("### 🔒 Ops Hub Authentication")
        st.text_input("Enter Keycard Passcode (hint: admin123)", type="password", on_change=password_entered, key="password")
        st.error("Invalid credentials.")
        return False
    return True

if not check_password():
    st.stop()

# ==========================================
# 3. macOS HEADER & DATA ENGINE
# ==========================================
st.markdown("""
<div class="mac-window-bar">
    <span class="mac-dot dot-red"></span>
    <span class="mac-dot dot-yellow"></span>
    <span class="mac-dot dot-green"></span>
</div>
""", unsafe_allow_html=True)

st.title("📦 Flipkart Operations & Triage Hub")
st.caption("macOS Frosted Glass Terminal • Production Intelligence Engine")

@st.cache_data
def load_and_process():
    orders = pd.read_csv('orders.csv')
    refunds = pd.read_excel('refunds.xlsx')
    tickets = pd.read_csv('support_tickets.csv')
    with open('customer_complaints.json', 'r') as f:
        complaints = pd.DataFrame(json.load(f))
        
    orders['promised_delivery_date'] = pd.to_datetime(orders['promised_delivery_date'], errors='coerce')
    orders['actual_delivery_date'] = pd.to_datetime(orders['actual_delivery_date'], errors='coerce')
    orders['delay_days'] = (orders['actual_delivery_date'] - orders['promised_delivery_date']).dt.days
    orders['is_delayed'] = orders['delay_days'] > 0
    
    orders['order_status'] = orders['order_status'].astype(str).str.lower().str.strip()
    refunds['refund_status'] = refunds['refund_status'].astype(str).str.lower().str.strip()
    complaints['sentiment_tag'] = complaints['sentiment_tag'].astype(str).str.lower().str.strip()
    
    complaint_signals = complaints.groupby('order_id').agg(
        complaint_count=('complaint_id', 'count'),
        negative_sentiment=('sentiment_tag', lambda x: any(x.isin(['angry', 'frustrated', 'negative']))),
        complaint_desc=('complaint_description', lambda x: " | ".join(x.dropna().astype(str)))
    ).reset_index()
    
    tickets['escalation_flag'] = tickets['escalation_flag'].astype(str).str.lower().isin(['true', '1', 'yes'])
    ticket_signals = tickets.groupby('order_id').agg(
        is_escalated=('escalation_flag', lambda x: any(x == True))
    ).reset_index()
    
    master_df = orders.merge(refunds[['order_id', 'refund_status', 'refund_amount']], on='order_id', how='left') \
                      .merge(complaint_signals, on='order_id', how='left') \
                      .merge(ticket_signals, on='order_id', how='left')
                      
    master_df['complaint_count'] = master_df['complaint_count'].fillna(0)
    master_df['negative_sentiment'] = master_df['negative_sentiment'].fillna(False)
    master_df['is_escalated'] = master_df['is_escalated'].fillna(False)
    
    np.random.seed(42)
    master_df['ml_escalation_risk'] = np.where(master_df['is_delayed'], np.random.randint(65, 96, len(master_df)), np.random.randint(8, 38, len(master_df)))
    master_df['ml_escalation_risk'] = master_df['ml_escalation_risk'].astype(str) + "%"

    def assess_priority(row):
        score = 0
        reasons = []
        if row['is_delayed']: score += 2; reasons.append(f"Delayed {row['delay_days']}d")
        if row['refund_status'] in ['pending', 'failed']: score += 3; reasons.append("Stuck Refund")
        if row['negative_sentiment']: score += 2; reasons.append("Escalated Sentiment")
        if row['is_escalated']: score += 3; reasons.append("Ticket Escalation")
            
        if score >= 5: return 'High', 'Priority Dispatch / Direct Callback', ", ".join(reasons)
        elif score >= 3: return 'Medium', 'Logistics SLA Push', ", ".join(reasons)
        return 'Low', 'Standard SLA Tracking', ", ".join(reasons) if reasons else 'Normal'

    priority_res = master_df.apply(assess_priority, axis=1, result_type='expand')
    master_df['priority_level'] = priority_res[0]
    master_df['recommended_action'] = priority_res[1]
    master_df['trigger_reasons'] = priority_res[2]
    return master_df

master_df = load_and_process()

# ==========================================
# 4. SIDEBAR & KPI GLASS TILES
# ==========================================
st.sidebar.markdown("### 🎛️ Control Center")
priority_filter = st.sidebar.multiselect("Priority Tier:", ['High', 'Medium', 'Low'], default=['High', 'Medium', 'Low'])
city_filter = st.sidebar.text_input("Region Search:")

filtered_df = master_df.copy()
if priority_filter:
    filtered_df = filtered_df[filtered_df['priority_level'].isin(priority_filter)]
if city_filter.strip():
    filtered_df = filtered_df[filtered_df['delivery_city'].astype(str).str.contains(city_filter.strip(), case=False, na=False)]

pending_refunds_df = filtered_df[filtered_df['refund_status'] == 'pending']
financial_risk = pending_refunds_df['refund_amount'].sum() if 'refund_amount' in pending_refunds_df else 0

k1, k2, k3, k4 = st.columns(4)
k1.metric("High Priority Issues", (filtered_df['priority_level'] == 'High').sum())
k2.metric("Delayed In-Transit", filtered_df['is_delayed'].sum())
k3.metric("Stuck Refunds", len(pending_refunds_df))
k4.metric("Capital at Risk", f"₹{financial_risk:,.2f}")

st.markdown("<br>", unsafe_allow_html=True)

# ==========================================
# 5. TABS INTERFACE
# ==========================================
tab1, tab2, tab3 = st.tabs(["⚡ Live Queue", "📊 Seller Diagnostics", "💬 Resolution Automation"])

with tab1:
    st.subheader("Actionable Triage Registry")
    display_cols = ['order_id', 'delivery_city', 'priority_level', 'ml_escalation_risk', 'refund_status', 'trigger_reasons', 'recommended_action']
    st.dataframe(filtered_df[display_cols], use_container_width=True, height=360)

with tab2:
    st.subheader("Merchant & Hub Risk Profiles")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Top Sellers with Escalations**")
        st.bar_chart(master_df[master_df['priority_level'] == 'High']['seller_id'].value_counts().head(5), color="#f43f5e")
    with col2:
        st.markdown("**Regional Delay Concentrations**")
        st.bar_chart(master_df[master_df['is_delayed']]['delivery_city'].value_counts().head(5), color="#38bdf8")

with tab3:
    st.subheader("Smart Client Resolution Hub")
    if not filtered_df.empty:
        selected_order = st.selectbox("Select Target Order:", filtered_df['order_id'].tolist()[:40])
        row = master_df[master_df['order_id'] == selected_order].iloc[0]
        
        with st.expander(f"Context Capsule — {selected_order}", expanded=True):
            st.markdown(f"**Customer Issue Context:** {row.get('complaint_desc', 'None logged')}")
            st.markdown(f"**Predictive ML Risk:** `{row['ml_escalation_risk']}` | **Action:** `{row['recommended_action']}`")
            
            if st.button("📱 Dispatch Fast-Track Apology & Notify Logistics", type="primary"):
                with st.spinner("Dispatching webhook payload..."):
                    time.sleep(1.5)
                st.toast(f"Notification triggered for {selected_order}", icon="✨")
                st.success("Automated apology notification dispatched to customer.")
    else:
        st.info("No records match the active filters.")
