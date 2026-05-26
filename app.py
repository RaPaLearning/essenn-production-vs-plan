import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st
import tempfile
from datetime import date, datetime
import io
import pandas as pd

from write_active_jobs import export_active_jobs


def main() -> None:
    st.set_page_config(
        page_title="Operations Extractor",
        page_icon="📊",
    )

    st.title("📊 Operations Extractor")
    st.write("Upload your XLSX file to extract and summarize operations by date")

    selected_date = st.date_input(
        "Select a date",
        value=datetime.now().date(),
        min_value=date(2020, 1, 1),
        format="DD-MM-YYYY",
    )

    uploaded_file = st.file_uploader("Choose an XLSX file", type="xlsx")

    if uploaded_file is not None:
        file_hash = f"{getattr(uploaded_file, 'file_id', uploaded_file.name)}_{uploaded_file.size}"
        state_key = f"processed_{file_hash}_{selected_date}"

        if state_key not in st.session_state:
            with st.spinner("Processing file..."):
                try:
                    with tempfile.TemporaryDirectory() as tmpdir:
                        input_path = Path(tmpdir) / "input.xlsx"
                        output_path = Path(tmpdir) / "output.xlsx"

                        input_path.write_bytes(uploaded_file.getvalue())

                        date_str = selected_date.strftime("%Y-%m-%d")
                        export_active_jobs(str(input_path), date_str, str(output_path))

                        st.session_state[state_key] = output_path.read_bytes()
                except Exception as e:
                    st.error(f"Error processing file: {e}")
                    return

        mime_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

        st.download_button(
            label="Download Summary Report",
            data=st.session_state[state_key],
            file_name=f"operations_summary_{selected_date}.xlsx",
            mime=mime_type,
        )

        st.subheader("Preview Summary")
        preview_df: pd.DataFrame = pd.read_excel(  # type: ignore[reportUnknownMemberType]
            io.BytesIO(st.session_state[state_key]),
            sheet_name="Shift I",
            header=5,
        )
        # Keep only the 7 data columns from the issue scope
        keep_cols = [
            "MACHINE",
            "JOB ORDER No",
            "TOTAL QTY",
            "PART NO",
            "PART NAME",
            "OPERATION",
            "PLAN QTY",
        ]
        preview_df = preview_df[[c for c in keep_cols if c in preview_df.columns]]
        # Drop rows that are not actual job data (sub-headers, blanks, signature rows)
        preview_df = preview_df.dropna(subset=["JOB ORDER No"])
        preview_df = preview_df[
            ~preview_df["JOB ORDER No"].astype(str).str.contains("Sign|None|OK|Rej", na=True)
        ]
        preview_df = preview_df.reset_index(drop=True)
        st.dataframe(preview_df, width="stretch")


if __name__ == "__main__":
    main()
