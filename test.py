import pandas as pd

df = pd.read_csv("./ml/data/raw/transactions.csv")

print(df.shape)
print(df.head())
print(df.dtypes)
print(df["is_fraud"].value_counts())
print(df["fraud_scenario"].value_counts())
print(df.groupby("is_fraud")["amount"].mean())
print(df.groupby("is_fraud")["account_age_days"].mean())
print(df.groupby("is_fraud")["transactions_last_hour"].mean())
print(df.groupby("is_fraud")["failed_transactions"].mean())