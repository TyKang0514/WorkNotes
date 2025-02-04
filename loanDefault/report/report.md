# Loan Default Risk Analysis
[Also find Jupyter Notebook here]()

## 0. OVERVIEW ##

This project explores various types of information extracted from loan application forms and identifies groups of features associated with a higher risk of default.

**Objective**
> Identify the features that contribute to an increased default rate.

**Methods**
>**Python Libraries** Pandas, Numpy, Seaborn, MatPlotLib

**Outcome**
>**Finding1** ... <br>
>**Finding2** ... <br>

## 1.About Dataset
**Sorce from Kaggle**

**Size**
>
>

**Attributes**
> **Key Variable** Default status (0:no default | 1: default) <br>
> **General Demographics** Gender, Family (number of dependents), Education<br>
> **Employment & Income** Income, Organization, Property ownership (housing and car)
> **Loan-related Information** Loan amount, Loan type, Loan purpose(objective goods)
>
> ***Note**: The actual dataset contains more detailed columns and uses different labels. The above grouping is a generalized representation for clarity*

## 2. Identify unnecessary column
### 2.1. Missing Value (49 columns deleted)
**Steps Taken**
> Remove columns with more than 40% missing values

**Code used** 
>```
># make a series of null value percentage of each column
>columnlist_null = df.isnull().sum() / df.shape[0] * 100
>
># make a list that contains the column which has more than 40% of null value
>column_unnecessary = columnlist_null[columnlist_null>40].index.tolist()
>```
