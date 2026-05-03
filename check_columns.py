import pandas as pd
df = pd.read_csv('data/raw/deliveries.csv')
print("DELIVERIES COLUMNS:")
print(df.columns.tolist())
print("\nFirst row:")
print(df.iloc[0])