# 🚀 Flipkart Operations & Triage Hub

An internal, Streamlit-based diagnostic dashboard designed for Flipkart's Marketplace Operations and Customer Support teams. This tool automates the integration of multiple data sources to identify delayed orders, prioritize pending refunds, analyze seller friction, and generate AI-ready support prompts.

## 🌟 Key Features

*   **🚦 Live Triage Queue:** An interactive, filterable data table that merges orders, refunds, support tickets, and customer complaints into a single actionable view.
*   **📊 Automated Priority Scoring:** Dynamically assigns High, Medium, or Low priority based on business rules (SLA breaches, angry customer sentiment, escalated tickets, and pending refunds).
*   **🏪 Seller Analytics:** Visual charts to identify top problematic sellers and refund concentration by category.
*   **🤖 AI Action Assistant (FR-13):** A built-in prompt generator that automatically structures context-rich prompts for Support Executives to copy-paste into LLMs for faster customer resolutions.
*   **📥 1-Click Export:** Download the fully filtered triage queue as a CSV report for offline processing.

## 🛠️ Tech Stack

*   **Frontend & UI:** [Streamlit](https://streamlit.io/)
*   **Data Processing:** Python, Pandas, NumPy
*   **Data Formats Handled:** CSV, Excel (`.xlsx`), JSON

## 📂 Project Structure

To run this dashboard, ensure the following files are in the same directory:

```text
📦 flipkart-operations-dashboard
 ┣ 📜 app.py                      # Main Streamlit application file
 ┣ 📜 requirements.txt            # Python dependencies
 ┣ 📜 orders.csv                  # Main order records
 ┣ 📜 refunds.xlsx                # Refund status and amounts
 ┣ 📜 support_tickets.csv         # Support escalations
 ┗ 📜 customer_complaints.json    # Customer feedback and sentiment
