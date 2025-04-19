import pandas as pd
import mysql.connector

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
  

    # only ARs that are created before report date
    report_date = pd.Timestamp(year=year, month=month, day=day)
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


    # Rename: Date > InvoiceDate columns
    AR_status = AR_status.rename(columns={'Date': 'InvoiceDate'})

    # filter collected
    AR_status = AR_status[AR_status['Residue'] != 0]

    return AR_status[['RefTransaction','Customer','InvoiceDate','PaymentDue','Charged','Collected','Residue']]

AR_status(2025,5,2).to_csv('AR_status.csv', index=False)


