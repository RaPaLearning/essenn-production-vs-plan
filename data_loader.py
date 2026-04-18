# type: ignore
import pandas as pd


def load_production_report() -> pd.DataFrame:
    df = pd.read_excel("data/sample/DailyProductionReport_17032026.xlsx")
    df["Date"] = pd.to_datetime(df["Date"], format="%Y%m%d")
    df["Start Time"] = pd.to_datetime(df["Start Time"], format="%d-%m-%Y %H:%M:%S")
    df["End Time"] = pd.to_datetime(df["End Time"], format="%d-%m-%Y %H:%M:%S")
    df = df.dropna(axis="columns", how="all")
    return df


def load_work_to_list() -> pd.DataFrame:
    xl = pd.ExcelFile("data/sample/WorkToListByResource.xlsx")
    all_sheets = []
    for sheet in xl.sheet_names:
        raw = pd.read_excel(xl, sheet_name=sheet, header=None)
        machine_name = raw.iloc[0, 0]
        df_sheet = pd.read_excel(xl, sheet_name=sheet, header=2)
        df_sheet = df_sheet.dropna(how="all").dropna(axis="columns", how="all")
        df_sheet.insert(0, "Machine", machine_name)
        all_sheets.append(df_sheet)
    return pd.concat(all_sheets, ignore_index=True)


def load_operations_by_day() -> pd.DataFrame:
    xl2 = pd.ExcelFile("data/sample/OperationsByDay.xlsx")
    all_days = []
    for sheet in xl2.sheet_names:
        raw = pd.read_excel(xl2, sheet_name=sheet, header=None)
        date_val = raw.iloc[1, 0]
        df_sheet = pd.read_excel(xl2, sheet_name=sheet, header=2)
        df_sheet = df_sheet.dropna(how="all").dropna(axis="columns", how="all")
        df_sheet.insert(0, "Date", date_val)
        all_days.append(df_sheet)
    return pd.concat(all_days, ignore_index=True)