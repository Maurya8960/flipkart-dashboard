import streamlit as st
import pandas as pd
import numpy as np
import json

# 1. Page Configuration
st.set_page_config(
    page_title="Flipkart Operations Hub",
    page_icon="📦",
    layout="wide"
)

st.title("📦 Flipkart Marketplace Operations & Triage Hub")
st.caption("Internal diagnostic engine for delay analysis, refund prioritization, and ticket escalations.")

# 2. Data Loading & Feature Engineering
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
    orders['delay_bucket'] = pd.cut(
        orders['delay_days'],
        bins=[-np.inf, 0, 2, 5, np.inf],
        labels=['On Time', '1-2 Days', '3-5 Days', 'Severe Delay']
    )
    
    orders['order_status'] = orders['order_status'].astype(str).str.lower().str.strip()
    refunds['refund_status'] = refunds['refund_status'].astype(str).str.lower().str.strip()
    complaints['sentiment_tag'] = complaints['sentiment_tag'].astype(str).str.lower().str.strip()
    
    # Aggregating Complaint Signals
    complaint_signals = complaints.groupby('order_id').agg(
        complaint_count=('complaint_id', 'count'),
        negative_sentiment=('sentiment_tag', lambda x: any(x.isin(['angry', 'frustrated', 'negative']))),
        complaint_desc=('complaint_description', lambda x: " | ".join(x.dropna().astype(str)))
    ).reset_index()
    
    # Aggregating Ticket Signals
    tickets['escalation_flag'] = tickets['escalation_flag'].astype(str).str.lower().isin(['true', '1', 'yes'])
    ticket_signals = tickets.groupby('order_id').agg(
        is_escalated=('escalation_flag', lambda x: any(x == True)),
        max_resolution_hours=('resolution_time_hours', 'max')
    ).reset_index()
    
    master_df = orders.merge(refunds[['order_id', 'refund_status', 'refund_amount']], on='order_id', how='left') \
                      .merge(complaint_signals, on='order_id', how='left') \
                      .merge(ticket_signals, on='order_id', how='left')
                      
    master_df['complaint_count'] = master_df['complaint_count'].fillna(0)
    master_df['negative_sentiment'] = master_df['negative_sentiment'].fillna(False)
    master_df['is_escalated'] = master_df['is_escalated'].fillna(False)
    
    # Dynamic Priority Scoring Engine (BR-01 to BR-08)
    def assess_priority(row):
        score = 0
        reasons = []
        if row['is_delayed']:
            score += 2
            reasons.append(f"Delayed by {row['delay_days']}d")
        if row['refund_status'] in ['pending', 'failed']:
            score += 3
            reasons.append(f"Refund {row['refund_status']}")
        if row['negative_sentiment']:
            score += 2
            reasons.append("Angry/Frustrated Sentiment")
        if row['is_escalated']:
            score += 3
            reasons.append("Escalated Ticket")
            
        if score >= 5:
            return 'High', score, 'Immediate Manager Intervention / Direct Callback', ", ".join(reasons)
        elif score >= 3:
            return 'Medium', score, 'Logistics SLA Push / Email Apology', ", ".join(reasons)
        return 'Low', score, 'Routine Tracking', ", ".join(reasons) if reasons else 'Normal Processing'

    priority_res = master_df.apply(assess_priority, axis=1, result_type='expand')
    master_df['priority_level'] = priority_res[0]
    master_df['priority_score'] = priority_res[1]
    master_df['recommended_action'] = priority_res[2]
    master_df['trigger_reasons'] = priority_res[3]
    return master_df

master_df = load_and_process()

# 3. Sidebar Navigation & Global Filters
st.sidebar.header("🎯 Operational Filters")
search_order = st.sidebar.text_input("Find by Order ID:", "").strip()
priority_filter = st.sidebar.multiselect("Priority Level:", ['High', 'Medium', 'Low'], default=['High', 'Medium', 'Low'])
city_filter = st.sidebar.text_input("Delivery City Filter:", "")
delay_bucket_filter = st.sidebar.multiselect("Delivery Status:", ['On Time', '1-2 Days', '3-5 Days', 'Severe Delay'], default=['On Time', '1-2 Days', '3-5 Days', 'Severe Delay'])

# Filter Execution
filtered_df = master_df.copy()
if search_order:
    filtered_df = filtered_df[filtered_df['order_id'].astype(str).str.contains(search_order, case=False, na=False)]
if priority_filter:
    filtered_df = filtered_df[filtered_df['priority_level'].isin(priority_filter)]
if delay_bucket_filter:
    filtered_df = filtered_df[filtered_df['delay_bucket'].isin(delay_bucket_filter)]
if city_filter.strip():
    filtered_df = filtered_df[filtered_df['delivery_city'].astype(str).str.contains(city_filter.strip(), case=False, na=False)]

# 4. Top KPI Cards
kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
kpi1.metric("📦 Filtered Orders", len(filtered_df))
kpi2.metric("⚠️ High Priority Cases", (filtered_df['priority_level'] == 'High').sum())
kpi3.metric("⏳ Delayed Shipments", filtered_df['is_delayed'].sum())
kpi4.metric("💳 Pending Refunds", (filtered_df['refund_status'] == 'pending').sum())
kpi5.metric("🚨 Escalated Tickets", filtered_df['is_escalated'].sum())

st.markdown("---")

# 5. Operational Analytics (Charts)
col_left, col_right = st.columns(2)
with col_left:
    st.subheader("🏙️ Top Problem Cities (High Priority)")
    city_counts = master_df[master_df['priority_level'] == 'High']['delivery_city'].value_counts().head(6)
    if not city_counts.empty:
        st.bar_chart(city_counts)
    else:
        st.info("No high priority city issues detected.")

with col_right:
    st.subheader("📊 Delivery Delays Breakdown")
    delay_counts = master_df['delay_bucket'].value_counts()
    st.bar_chart(delay_counts)

st.markdown("---")

# 6. Primary Actionable Table
st.subheader("📋 Triage Queue & Escalation Matrix")
display_cols = [
    'order_id', 'delivery_city', 'order_status', 'priority_level', 
    'priority_score', 'delay_bucket', 'refund_status', 'trigger_reasons', 'recommended_action'
]
st.dataframe(filtered_df[display_cols], use_container_width=True, height=360)

# Export Control
csv_data = filtered_df.to_csv(index=False).encode('utf-8')
st.download_button(
    label="📥 Download Full Incident Resolution Report (CSV)",
    data=csv_data,
    file_name='flipkart_operations_resolution_report.csv',
    mime='text/csv'
)

st.markdown("---")

# 7. FR-13: AI Assistant Prompt Generator
st.subheader("🤖 Support Executive AI Prompt Generator (FR-13)")
st.caption("Generate pre-formatted contextual prompts to quickly run customer outreach via any LLM without manual drafting.")

if not filtered_df.empty:
    selected_order = st.selectbox("Select an Order from filtered results:", filtered_df['order_id'].tolist()[:30])
    row = master_df[master_df['order_id'] == selected_order].iloc[0]
    
    prompt_text = f"""[FLIPKART SUPPORT ACTION TICKET]
Order ID: {row['order_id']}
Delivery City: {row['delivery_city']}
Current Status: {row['order_status']}
Delay Days: {row['delay_days']} ({row['delay_bucket']})
Refund Status: {row['refund_status']} (Amount: ₹{row.get('refund_amount', 'N/A')})
Risk Signals: {row['trigger_reasons']}
Recommended Strategy: {row['recommended_action']}
Customer Issue Context: {row.get('complaint_desc', 'None logged')}

Instructions for AI: Draft an empathetic, solution-oriented resolution message addressed to this customer acknowledging our logistics failure and providing immediate next steps."""

    st.text_area("Generated Contextual Prompt (Ready to Copy):", value=prompt_text, height=220)
else:
    st.info("No orders found matching the filter criteria.")
