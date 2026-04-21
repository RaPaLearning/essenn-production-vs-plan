import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st  # pragma: no cover
import tempfile  # pragma: no cover
from datetime import date, datetime  # pragma: no cover

from get_active_jobs import export_active_jobs


def main() -> None:  # pragma: no cover
    st.set_page_config(  # pragma: no cover
        page_title="Operations Extractor",  # pragma: no cover
        page_icon="📊",  # pragma: no cover
    )  # pragma: no cover

    st.title("📊 Operations Extractor")  # pragma: no cover
    st.write(
        "Upload your XLSX file to extract and summarize operations by date"
    )  # pragma: no cover

    selected_date = st.date_input(  # pragma: no cover
        "Select a date",
        value=datetime.now().date(),
        min_value=date(2020, 1, 1),  # pragma: no cover
    )  # pragma: no cover

    uploaded_file = st.file_uploader("Choose an XLSX file", type="xlsx")  # pragma: no cover

    if uploaded_file is not None:  # pragma: no cover
        file_hash = f"{getattr(uploaded_file, 'file_id', uploaded_file.name)}_{uploaded_file.size}"
        state_key = f"processed_{file_hash}_{selected_date}"

        if state_key not in st.session_state:
            with st.spinner("Processing file..."):
                try:  # pragma: no cover
                    with tempfile.TemporaryDirectory() as tmpdir:
                        input_path = Path(tmpdir) / "input.xlsx"
                        output_path = Path(tmpdir) / "output.xlsx"

                        input_path.write_bytes(uploaded_file.getvalue())

                        date_str = selected_date.strftime("%Y-%m-%d")
                        export_active_jobs(str(input_path), date_str, str(output_path))

                        st.session_state[state_key] = output_path.read_bytes()
                except Exception as e:  # pragma: no cover
                    st.error(f"Error processing file: {e}")  # pragma: no cover
                    return  # pragma: no cover

        mime_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        st.download_button(  # pragma: no cover
            label="Download Summary Report",  # pragma: no cover
            data=st.session_state[state_key],  # pragma: no cover
            file_name=f"operations_summary_{selected_date}.xlsx",  # pragma: no cover
            mime=mime_type,  # pragma: no cover
        )  # pragma: no cover


if __name__ == "__main__":  # pragma: no cover
    main()  # pragma: no cover
