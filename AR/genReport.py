import streamlit as st
import datetime
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt 
import plotly.graph_objects as go

url = 'https://raw.githubusercontent.com/TyKang0514/WorkNotes/refs/heads/main/AR/AR_status.csv'
arstat = pd.read_csv(url)

# Set page config (optional)
st.set_page_config(layout="wide")
st.title("AR Status Report")


# Make the columns more narrow
col1, col2, col3, _ = st.columns([1, 1, 1, 6])  # Last one fills the rest space

with col1:
    year = st.selectbox("Year", list(range(2020, 2031)), index=5)
with col2:
    month = st.selectbox("Month", list(range(1, 13)))
with col3:
    day = st.selectbox("Day", list(range(1, 32)))


# Submit button
if st.button("Generate Report"):
    try:
        # filter date
        date = datetime.date(year, month, day)
        arstat['InvoiceDate'] = pd.to_datetime(arstat['InvoiceDate'])
        arstat['InvoiceDate'] = arstat['InvoiceDate'].dt.date
        arstat = arstat[arstat['InvoiceDate'] <= date]

        # success message
        st.success(f"Report generated for {date}")

        # Summary page
        st.subheader("Summary")
        
        ## Calculate
        total = arstat['Residue'].sum()
        normal = arstat[arstat['Status'] == "Normal"]['Residue'].sum()
        overdue = arstat[arstat['Status'] == "Overdue"]['Residue'].sum()
        poor = arstat[arstat['Status'] == "Poor"]['Residue'].sum()

        ## Avoid division by zero
        def percent(part):
            return f"{(part / total * 100):.1f}%" if total != 0 else "0.0%"

        # Layout with 4 columns
        col1, col2, col3, col4 = st.columns(4)
        col1.markdown(f"**Total AR Amount (USD)**<br><span style='font-size:24px'>{total:,.0f}</span>", unsafe_allow_html=True)
        col2.markdown(f"**🟩 Normal**<br><span style='font-size:20px'>{normal:,.0f}</span><br><span style='color:#4CAF50'>{percent(normal)}</span>", unsafe_allow_html=True)
        col3.markdown(f"**🟧 Overdue**<br><span style='font-size:20px'>{overdue:,.0f}</span><br><span style='color:#FF9800'>{percent(overdue)}</span>", unsafe_allow_html=True)
        col4.markdown(f"**🟥 Poor**<br><span style='font-size:20px'>{poor:,.0f}</span><br><span style='color:#F44336'>{percent(poor)}</span>", unsafe_allow_html=True)

        # Visualization (Horizontal stacked bar using Plotly)
        statuses = ['Normal', 'Overdue', 'Poor']
        values = [normal, overdue, poor]
        colors = ['#4CAF50', '#FF9800', '#F44336']
        percentages = [v / sum(values) * 100 if sum(values) > 0 else 0 for v in values]

        fig = go.Figure()

        # Add each status as a bar segment
        for status, val, color, pct in zip(statuses, values, colors, percentages):
            fig.add_trace(go.Bar(x=[pct], y=[""],
                orientation='h',
                marker=dict(color=color),
                hovertemplate=f'{status}: {val:,.0f} ({pct:.1f}%)<extra></extra>'))

        # Clean layout
        fig.update_layout(barmode='stack', height=80,
                          margin=dict(l=0, r=150, t=30, b=0), showlegend=False)

        st.plotly_chart(fig, use_container_width=True)

        st.markdown('---')

        st.subheader("AR by Customers")
        st.dataframe(arstat.reset_index(drop=True), use_container_width=True, height=300)

        # Define custom styling function
        def highlight_status(val):
            if val == 'Poor':
                return 'color: white; background-color: red'
            elif val == 'Overdue':
                return 'color: white; background-color: orange'
            return ''

        # Apply styling only to the 'status' column
        styled_df = arstat.style.applymap(highlight_status, subset=['Status'])

        # Display in Streamlit
        st.subheader("AR by Customers_colored")
        st.dataframe(styled_df, use_container_width=True, height=300)


        


    except ValueError:
        st.error("Invalid date! Please select a valid day for the month.")
