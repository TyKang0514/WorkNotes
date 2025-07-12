SELECT 
    GL.RefTransaction, 
    GL.CustomerID, 
    GL.Customer, 
    GL.Date, 
    Customer.PaymentTerm, 
    Aggregated.Charged, 
    Aggregated.Collected, 
    Aggregated.Residue
FROM GL
LEFT JOIN Customer 
    ON GL.CustomerID = Customer.CustomerID
LEFT JOIN (
    SELECT 
        RefTransaction, 
        SUM(Debit) AS Charged, 
        SUM(Credit) AS Collected, 
        SUM(Debit) - SUM(Credit) AS Residue
    FROM GL 
    GROUP BY RefTransaction
) AS Aggregated
    ON GL.RefTransaction = Aggregated.RefTransaction
WHERE GL.DebitCredit = 'D'
  AND Aggregated.Residue > 0;
