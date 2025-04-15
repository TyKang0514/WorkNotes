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
col1, col2, col3, _ = st.columns([1, 1, 1, 6])  
# Last one fills the rest space
with col1:
    year = st.selectbox("Year", list(range(2020, 2031)), index=5)
with col2:
    month = st.selectbox("Month", list(range(1, 13)), index=4)
with col3:
    day = st.selectbox("Day", list(range(1, 32)), index=1)


# Submit button

if "report_generated" not in st.session_state:
    st.session_state.report_generated = False
if st.button("Generate Report"):
    st.session_state.report_generated = True
if st.session_state.report_generated:
    try:
        # filter date
        date = datetime.date(year, month, day)
        arstat['PaymentDue'] = pd.to_datetime(arstat['PaymentDue'], errors='coerce').dt.date
        arstat['OverdueDays'] = (date - arstat['PaymentDue']).apply(lambda x: x.days if pd.notnull(x) else None)
        arstat['InvoiceDate'] = pd.to_datetime(arstat['InvoiceDate'])
        arstat['InvoiceDate'] = arstat['InvoiceDate'].dt.date
        arstat = arstat[arstat['InvoiceDate'] <= date]
        arstat = arstat[['RefTransaction', 'Customer', 'InvoiceDate', 'PaymentDue', 'OverdueDays', 
                         'Charged', 'Collected', 'Residue' ]]
        

        # success message
        st.success(f"Report generated for {date}")

        #1 Summary page
        st.subheader("Aging Summary (USD)")
        
        ##1.1 Calculate
        total = arstat['Residue'].sum()
        normal = arstat[arstat['OverdueDays'] <= 0]['Residue'].sum()
        pending = arstat[(arstat['OverdueDays'] > 0)& (arstat['OverdueDays'] <= 30)]['Residue'].sum()
        risky = arstat[arstat['OverdueDays'] > 30]['Residue'].sum()

        ##1.2. Show AR amount
        def percent(part):
            return f"{(part / total * 100):.1f}%" if total != 0 else "0.0%"

        col1, col2, col3, col4 = st.columns(4)
        col1.markdown(f"**Total AR Amount**<br><span style='font-size:24px'>{total:,.0f}</span>", unsafe_allow_html=True)
        col2.markdown(f"**🟩 Normal**<br><span style='font-size:20px'>{normal:,.0f}</span><br><span style='color:#4CAF50'>{percent(normal)}</span>", unsafe_allow_html=True)
        col3.markdown(f"**🟧 Pending (D+1 ~ D+30)**<br><span style='font-size:20px'>{pending:,.0f}</span><br><span style='color:#FF9800'>{percent(pending)}</span>", unsafe_allow_html=True)
        col4.markdown(f"**🟥 Risky (D+31 ~ )**<br><span style='font-size:20px'>{risky:,.0f}</span><br><span style='color:#F44336'>{percent(risky)}</span>", unsafe_allow_html=True)

        ##1.3 Visualization (Horizontal stacked bar using Plotly)
        statuses = ['Normal', 'Pending', 'Risky']
        values = [normal, pending, risky]
        colors = ['#94cba8', '#f9d89c', '#f99e8b']
        percentages = [v / sum(values) * 100 if sum(values) > 0 else 0 for v in values]

        fig = go.Figure()

        for status, val, color, pct in zip(statuses, values, colors, percentages):
            fig.add_trace(go.Bar(x=[pct], y=[""],
                orientation='h',
                marker=dict(color=color),
                hovertemplate=f'{status}: {val:,.0f} ({pct:.1f}%)<extra></extra>'))

        fig.update_layout(barmode='stack', height=80,
                          margin=dict(l=0, r=30, t=30, b=0), showlegend=False)

        st.plotly_chart(fig, use_container_width=True)

        st.markdown('---')

        #2 details
        st.subheader("AR Details")
        col1, col2, col3 = st.columns([1, 3, 1])  
        with col1:
            category = st.selectbox("AR status", ["All", "Normal", "Pending", "Risky", "Pending + Risky"], label_visibility="collapsed")
            
        if category == "Normal":
            filtered_arstat = arstat[arstat['OverdueDays'] <= 0]
        elif category == "Pending":
            filtered_arstat = arstat[(arstat['OverdueDays'] > 0) & (arstat['OverdueDays'] <= 30)]
        elif category == "Risky":
            filtered_arstat = arstat[arstat['OverdueDays'] > 30]
        elif category == "Pending + Risky":
            filtered_arstat = arstat[arstat['OverdueDays'] > 0]
        else:
            filtered_arstat = arstat  # All

       # Display subtotal in the second column (next to the scroll list)
        subtotal = filtered_arstat['Residue'].sum()
        with col3:
            st.markdown(f"**Residue Total_USD**<br><span style='font-size:20px'>  {subtotal:,.0f}</span>", unsafe_allow_html=True)

        #col4.markdown(f"**🟥 Risky (D+31 ~ )**<br><span style='font-size:20px'>{risky:,.0f}</span><br><span style='color:#F44336'>{percent(risky)}</span>", unsafe_allow_html=True)

        def color_overdue(val):
            if val <= 0:
                return 'background-color: #94cba8'  # light green for Normal
            elif 0 < val <= 30:
                return 'background-color: #f9d89c'  # light orange for Pending
            else:
                return 'background-color: #f99e8b'  # light red for Risky
            
        styled_df = filtered_arstat.style.applymap(color_overdue, subset=['OverdueDays'])
        styled_df = styled_df.format({'Residue': '{:,.0f}', 'Charged': '{:,.0f}', 'Collected': '{:,.0f}'})
        st.dataframe(styled_df, use_container_width=True, height=300)

    except ValueError:
        st.error("Invalid date! Please select a valid day for the month.")

