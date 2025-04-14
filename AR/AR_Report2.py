import streamlit as st
import datetime
import pandas as pd
import mysql.connector
import seaborn as sns
import matplotlib.pyplot as plt 
import plotly.graph_objects as go

# Establish a connection to MySQL
conn = mysql.connector.connect(
    host="localhost",         # Local MySQL server
    user="root",              # MySQL username
    password="circle07!@", # Replace with your MySQL password
    database="AR"  # Replace with your database name
)

# Use pandas read_sql() to execute query and load data into DataFrame
gl = pd.read_sql("SELECT * FROM GL", conn)  
cm = pd.read_sql("SELECT * FROM Customer", conn)  
residue = pd.read_sql('''
    SELECT 
        GL.RefTransaction, GL.CustomerID, GL.Customer, GL.Date, Customer.PaymentTerm, 
        Aggregated.Charged, Aggregated.Collected, Aggregated.Residue
    FROM GL
    LEFT JOIN Customer ON GL.CustomerID = Customer.CustomerID
    LEFT JOIN 
        (SELECT RefTransaction, 
                SUM(Debit) AS Charged, SUM(Credit) AS Collected, SUM(Debit) - SUM(Credit) AS Residue
         FROM GL GROUP BY RefTransaction
        ) AS Aggregated
    ON GL.RefTransaction = Aggregated.RefTransaction
    WHERE GL.DebitCredit = 'D' ''', conn)
conn.close()


def AR_status(year,month,day):
    AR_status = residue.copy()
    report_date = pd.Timestamp(year=year, month=month, day=day)

    #only ARs that are created before report date
    # Renaming specific columns
    AR_status['Date'] = pd.to_datetime(AR_status['Date'])
    AR_status = AR_status[AR_status['Date'] <= report_date]

    #generate paymentdue column
    def payment_due(row):
        # Add one month to the current date
        next_month_date = row['Date'] + pd.DateOffset(months=1)
        
        if row['PaymentTerm'] < 30:
            # Set the PaymentDue to next month with the same day as PaymentTerm
            return next_month_date.replace(day=row['PaymentTerm'])
        else:
            # If PaymentTerm is 30 or more, calculate the last day of the next month
            due = pd.Timestamp(next_month_date.year, next_month_date.month, 1) + pd.DateOffset(months=1, days=-1)
            if row['PaymentTerm'] == 30:
                return due
            elif row['PaymentTerm'] == 60:
                # For PaymentTerm 60, set to last day of next next month
                due = pd.Timestamp(next_month_date.year, next_month_date.month, 1) + pd.DateOffset(months=2, days=-1)
                return due
            elif row['PaymentTerm'] == 90:
                # For PaymentTerm 60, set to last day of next next month
                due = pd.Timestamp(next_month_date.year, next_month_date.month, 1) + pd.DateOffset(months=3, days=-1)
                return due
    
    AR_status['PaymentDue'] = AR_status.apply(payment_due, axis=1)

    #generate overduedays column
    AR_status['OverdueDays'] = (report_date - AR_status['PaymentDue']).dt.days

    #generate status column
    AR_status['Status'] = AR_status.apply(
    lambda row: 'Collected' if row['Residue']==0 
        else 'Normal' if row['OverdueDays'] <= 0 
        else 'Overdue' if row['OverdueDays'] <= 30 
        else 'Poor',
    axis=1)

    # Rename: Date > InvoiceDate columns
    AR_status = AR_status.rename(columns={'Date': 'InvoiceDate'})

    # filter collected
    AR_status = AR_status[AR_status['Status'] != 'Collected']

    return AR_status[['RefTransaction','Customer','InvoiceDate','PaymentDue','OverdueDays','Charged','Collected','Residue','Status']]




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
        # 🗓️ Validate the date (in case of invalid ones like Feb 30)
        date = datetime.date(year, month, day)
        
        # 🚀 Run your function
        arstat = AR_status(year, month, day)
        arstat['InvoiceDate'] = arstat['InvoiceDate'].dt.strftime('%Y-%m-%d')
        arstat['PaymentDue'] = arstat['PaymentDue'].dt.strftime('%Y-%m-%d')

        st.success(f"Report generated for {date}")

        st.subheader("Summary")

        # Calculate
        total = gl['Debit'].sum() - gl['Credit'].sum()
        normal = arstat[arstat['Status'] == "Normal"]['Residue'].sum()
        overdue = arstat[arstat['Status'] == "Overdue"]['Residue'].sum()
        poor = arstat[arstat['Status'] == "Poor"]['Residue'].sum()

        # Avoid division by zero
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
