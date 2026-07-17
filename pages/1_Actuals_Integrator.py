"""Step 3: Actuals Integrator page."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st

from actuals_integrator import process_actuals


def _handle_integrator(
    summary_file: st.runtime.uploaded_file_manager.UploadedFile,  # type: ignore[reportUnknownParameterType]
    tpm_files: list,  # type: ignore[reportMissingTypeArgument]
) -> None:
    """Process the integrator upload and render results."""
    s_hash = (
        f"{getattr(summary_file, 'file_id', summary_file.name)}"  # type: ignore[reportUnknownArgumentType, reportUnknownMemberType]
        f"_{summary_file.size}"  # type: ignore[reportUnknownMemberType]
    )
    t_hash = "_".join(
        str(getattr(f, "file_id", f.name))  # type: ignore[reportUnknownArgumentType, reportUnknownMemberType, reportUnknownVariableType]
        for f in tpm_files  # type: ignore[reportUnknownVariableType]
    )
    state_key = f"integrated_{s_hash}_{t_hash}"

    if state_key not in st.session_state:
        with st.spinner("Integrating actuals..."):
            try:
                summary_bytes: bytes = summary_file.getvalue()  # type: ignore[reportUnknownMemberType]
                tpm_bytes_list: list[bytes] = [
                    f.getvalue()  # type: ignore[reportUnknownMemberType, reportUnknownVariableType]
                    for f in tpm_files  # type: ignore[reportUnknownVariableType]
                ]
                st.session_state[state_key] = process_actuals(
                    summary_bytes,  # type: ignore[reportUnknownArgumentType]
                    tpm_bytes_list,
                )
                st.success("Actuals integrated successfully!")
            except Exception as e:
                st.error(f"Error integrating actuals: {e}")
                return

    mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    out_name = str(summary_file.name).replace(".xlsx", "_with_actuals.xlsx")  # type: ignore[reportUnknownMemberType]
    st.download_button(
        label="Download Updated Summary",
        data=st.session_state[state_key],
        file_name=out_name,
        mime=mime,
    )


def main() -> None:
    """Render the Actuals Integrator page."""
    st.set_page_config(
        page_title="Actuals Integrator",
        page_icon="🔗",
    )

    if st.button("← Back to Home"):
        st.switch_page("app.py")

    st.title("🔗 Actuals Integrator")
    st.write(
        "Upload your Operations Summary and TPM IoT data"
        " files to auto-fill actual production quantities.",
    )

    summary_file = st.file_uploader(
        "Upload Operations Summary (Step 2 output)",
        type="xlsx",
        key="integrator_summary",
    )
    tpm_files = st.file_uploader(
        "Upload TPM Data Files",
        type="xlsx",
        accept_multiple_files=True,
        key="integrator_tpm",
    )

    if summary_file and tpm_files:
        _handle_integrator(summary_file, tpm_files)


if __name__ == "__main__":
    main()
