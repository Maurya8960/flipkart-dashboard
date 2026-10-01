import streamlit as st
import pandas as pd
import numpy as np
import json
import io

# 1. Page Configuration
st.set_page_config(page_title="Flipkart Operations Dashboard", layout="wide")
st.title("🚀 Flipkart Operations Live Dashboard")

# 2. Data Loading & Processing (Cached for speed)
@st.cache_data
def load_process_data():
    # Load actual files
    orders = pd.read_csv('orders.csv')
    refunds = pd.read_excel('refunds.xlsx')
    tickets = pd.read_csv('support_tickets.csv')
    
    with open('customer_complaints.json', 'r') as f:
        complaints = pd.DataFrame(json.load(f))
        
    # Process dates & delay
    orders['promised_delivery_date'] = pd.to_datetime(orders['promised_delivery_date'], errors='coerce')
    orders['actual_delivery_date'] = pd.to_datetime(orders['actual_delivery_date'], errors='coerce')
    orders['delay_days'] = (orders['actual_delivery_date'] - orders['promised_delivery_date']).dt.days
    orders['is_delayed'] = orders['delay_days'] > 0
    orders['delay_bucket'] = pd.cut(
        orders['delay_days'],
        bins=[-np.inf, 0, 2, 5, np.inf],
        labels=['On Time', '1-2 Days', '3-5 Days', 'Severe Delay']
    )
    
    # Standardize casing
    orders['order_status'] = orders['order_status'].astype(str).str.lower().str.strip()
    refunds['refund_status'] = refunds['refund_status'].astype(str).str.lower().str.strip()
    complaints['sentiment_tag'] = complaints['sentiment_tag'].astype(str).str.lower().str.strip()
    
    # Aggregations
    complaint_signals = complaints.groupby('order_id').agg(
        complaint_count=('complaint_id', 'count'),
        negative_sentiment=('sentiment_tag', lambda x: any(x.isin(['angry', 'frustrated', 'negative'])))
    ).reset_index()
    
    tickets['escalation_flag'] = tickets['escalation_flag'].astype(str).str.lower().isin(['true', '1', 'yes'])
    ticket_signals = tickets.groupby('order_id').agg(
        is_escalated=('escalation_flag', lambda x: any(x == True)),
        max_resolution_hours=('resolution_time_hours', 'max')
    ).reset_index()
    
    # Master Table
    master_df = orders.merge(refunds[['order_id', 'refund_status', 'refund_amount']], on='order_id', how='left') \
                      .merge(complaint_signals, on='order_id', how='left') \
                      .merge(ticket_signals, on='order_id', how='left')
                      
    master_df['complaint_count'] = master_df['complaint_count'].fillna(0)
    master_df['negative_sentiment'] = master_df['negative_sentiment'].fillna(False)
    master_df['is_escalated'] = master_df['is_escalated'].fillna(False)
    
    # Priority Logic
    def assess_priority(row):
        score = 0
        if row['is_delayed']: score += 2
        if row['refund_status'] in ['pending', 'failed']: score += 3
        if row['negative_sentiment']: score += 2
        if row['is_escalated']: score += 3
        
        if score >= 5: return 'High', 'Immediate refund review / Call customer'
        elif score >= 3: return 'Medium', 'Logistics escalation & delay notification'
        return 'Low', 'Standard SLA tracking'

    master_df[['priority_level', 'recommended_action']] = master_df.apply(assess_priority, axis=1, result_type='expand')
    return master_df

master_df = load_process_data()

# 3. Sidebar Filters
st.sidebar.header("🔍 Filter Options")
priority_filter = st.sidebar.selectbox("Select Priority:", ['All', 'High', 'Medium', 'Low'])
city_filter = st.sidebar.text_input("Delivery City (e.g., Delhi):", "")

# 4. Filter Logic
filtered_df = master_df.copy()
if priority_filter != 'All':
    filtered_df = filtered_df[filtered_df['priority_level'] == priority_filter]
if city_filter.strip():
    filtered_df = filtered_df[filtered_df['delivery_city'].astype(str).str.contains(city_filter.strip(), case=False, na=False)]

# 5. Top KPIs
st.markdown("### 📊 Overall Health Summary")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Analyzed", len(master_df))
c2.metric("Delayed Shipments", master_df['is_delayed'].sum())
c3.metric("High Priority Cases", (master_df['priority_level'] == 'High').sum())
c4.metric("Pending Refunds", (master_df['refund_status'] == 'pending').sum())
st.markdown("---")

# 6. Display Table
display_cols = ['order_id', 'delivery_city', 'order_status', 'priority_level', 'delay_bucket', 'refund_status', 'recommended_action']
st.dataframe(filtered_df[display_cols], use_container_width=True)

# 7. Export Button
csv = filtered_df.to_csv(index=False).encode('utf-8')
st.download_button(
    label="⬇️ Export Filtered Data to CSV",
    data=csv,
    file_name='flipkart_operations_report.csv',
    mime='text/csv',
)