from datetime import datetime

from get_active_jobs import export_active_jobs

date_str = "2026-03-10"

# Convert "2026-03-15" -> "15-03-2026.xlsx"
date_obj = datetime.strptime(date_str, "%Y-%m-%d")
output_file = date_obj.strftime("%d-%m-%Y") + ".xlsx"

export_active_jobs("tests/fixtures/test_operations.xlsx", date_str, output_file)
# The above line inputs test_operations.xlsx. To input operations.xlsx use the below line
# export_active_jobs("data/sample/OperationsByDay.xlsx", date_str, output_file)
print(f"Exported to {output_file}")
