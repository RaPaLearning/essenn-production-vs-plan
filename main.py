import pandas as pd
from src.standardize import standardize_dataframe


def load_plan_data(path: str) -> pd.DataFrame:
    sheets = pd.read_excel(path, sheet_name=None)
    data = []

    for sheet_name, df in sheets.items():
        if df.empty:
            continue

        df.columns = df.iloc[4]
        df = df.iloc[5:].reset_index(drop=True)

       
        new_cols = []
        for i, col in enumerate(df.columns):
            if pd.isna(col) or str(col).strip() == "":
                new_cols.append(f"_unnamed_{i}")
            else:
                new_cols.append(str(col).strip())

    
        seen = {}
        deduped = []
        for col in new_cols:
            if col in seen:
                seen[col] += 1
                deduped.append(f"{col}_{seen[col]}")
            else:
                seen[col] = 0
                deduped.append(col)

        df.columns = deduped
        data.append(df)

    return pd.concat(data, ignore_index=True)


def load_production_data(path: str) -> pd.DataFrame:
    df = pd.read_excel(path)

    for col in df.columns:
        if "order" in str(col).lower():
            df.rename(columns={col: "Order No"}, inplace=True)

    return df


def main():
    plan = load_plan_data("data/sample/OperationsByDay.xlsx")
    production = load_production_data("data/sample/DailyProductionReport_17032026.xlsx")

    plan_clean = standardize_dataframe(plan)
    production_clean = standardize_dataframe(production)

    # Save cleaned files
    plan_clean.to_excel("clean_plan.xlsx", index=False)
    production_clean.to_excel("clean_production.xlsx", index=False)

    print("Standardization complete and files saved.")


if __name__ == "__main__":
    main()