import pandas as pd
from data_loader import load_production_report, load_work_to_list, load_operations_by_day

# Load — date cleaning already happens inside load_production_report()
df: pd.DataFrame = load_production_report()

print("\nCleaned data:")
print(df["Date"].head(3))
print(df[["Start Time", "End Time"]].head(3))
print(df[["Date", "Start Time", "End Time"]].dtypes)

print("\nEmpty columns:")
print(df.isnull().sum()[df.isnull().sum() == len(df)])

plan_df: pd.DataFrame = load_work_to_list()
print("\nWork to list shape:", plan_df.shape)
print(plan_df.head())

ops_df: pd.DataFrame = load_operations_by_day()
print("\nOperations by day shape:", ops_df.shape)
print(ops_df.head())