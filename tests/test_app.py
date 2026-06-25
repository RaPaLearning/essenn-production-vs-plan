import logging
import os
import unittest
from datetime import date
from streamlit.testing.v1 import AppTest

# Suppress all Streamlit stderr noise (logging + raw pyarrow tracebacks).
logging.getLogger("streamlit").setLevel(logging.ERROR)


class TestApp(unittest.TestCase):
    def setUp(self) -> None:
        """Redirect the OS-level stderr fd to devnull to silence pyarrow tracebacks."""
        self._orig_stderr_fd = os.dup(2)
        self._devnull_fd = os.open(os.devnull, os.O_WRONLY)
        os.dup2(self._devnull_fd, 2)

    def tearDown(self) -> None:
        """Restore the OS-level stderr fd after each test."""
        os.dup2(self._orig_stderr_fd, 2)
        os.close(self._orig_stderr_fd)
        os.close(self._devnull_fd)

    def test_app_loads_and_processes_file(self):
        """Test the Streamlit app logic from loading to file download using AppTest naturally."""
        # Initialize the app test pointing to our main app script
        at = AppTest.from_file("app.py", default_timeout=30)
        at.run()

        # Verify that the app loaded correctly without any immediate crashes
        self.assertFalse(at.exception, f"App failed to load: {at.exception}")

        # Verify main UI elements are present
        self.assertEqual(at.title[0].value, "📊 Operations Extractor")

        # Verify baseline UI state (no download button should be shown initially)
        has_unknown_elements = any(
            getattr(e, "type", type(e).__name__) == "UnknownElement" for e in at.main
        )
        self.assertFalse(
            has_unknown_elements,
            "Download button element should not exist before an upload is completed",
        )
        self.assertEqual(len(at.subheader), 0, "Preview subheader should not exist initially")
        self.assertEqual(len(at.dataframe), 0, "Dataframe preview should not exist initially")

        # Find sample data
        sample_path = "data/sample/OperationsByDay.xlsx"
        self.assertTrue(os.path.exists(sample_path), f"Sample file not found at {sample_path}")

        with open(sample_path, "rb") as f:
            file_bytes = f.read()

        # Set the target date and trigger a stream re-run
        target_date = date(2026, 3, 16)
        at.date_input[0].set_value(target_date).run()
        self.assertFalse(at.exception, "App crashed while setting date")

        # Simulate uploading the file via the file uploader component
        # Streamlit AppTest expects a list of tuples containing (filename, content_bytes, mime_type)
        mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        at.file_uploader[0].set_value([("OperationsByDay.xlsx", file_bytes, mime)]).run()

        # Verify that processing the mock file didn't crash the Streamlit app script
        self.assertFalse(at.exception, f"App crashed during file processing: {at.exception}")

        # The main validation: check if the download button (UnknownElement subtype)
        # was appended to the bottom and it only renders if the file processing runs completely
        # without hitting earlier exceptions and correctly saves bytes to session_state.
        has_download_button = any(
            getattr(e, "type", type(e).__name__) == "download_button" for e in at.main
        )
        self.assertTrue(
            has_download_button,
            "Download button element was not rendered into the tree (processing failed)",
        )

        # Verify the preview subheader and dataframe element are rendered successfully
        self.assertGreater(len(at.subheader), 0, "Preview subheader should be rendered")
        self.assertEqual(at.subheader[0].value, "Preview Summary")
        self.assertGreater(len(at.dataframe), 0, "Dataframe preview should be rendered")

    def test_app_handles_invalid_file(self):
        """Test that uploading a completely invalid file gets caught naturally.

        This tests the except block to ensure there are no crashes in AppTest.
        """
        at = AppTest.from_file("app.py", default_timeout=30)
        at.run()

        # Uploading raw text bytes mapped to an excel mime to trigger pandas crash artificially
        bad_bytes = b"This is definitely not an excel file."
        mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        at.file_uploader[0].set_value([("bad_data.xlsx", bad_bytes, mime)]).run()

        # Verify the application itself did NOT crash natively
        self.assertFalse(
            at.exception,
            f"App completely crashed instead of gracefully handling the exception: {at.exception}",
        )

        # It should hit the st.error block
        self.assertGreater(
            len(at.error), 0, "Expected an st.error block to render when processing fails"
        )
        self.assertIn(
            "Error processing file",
            at.error[0].value,
            "The error message did not match expectations",
        )

        # The download button must NOT exist.
        has_download_button = any(
            getattr(e, "type", type(e).__name__) == "download_button" for e in at.main
        )
        self.assertFalse(
            has_download_button, "A download button was improperly rendered after a failure"
        )

        # The preview components must NOT exist
        self.assertEqual(
            len(at.subheader), 0, "Preview subheader should not be rendered after a failure"
        )
        self.assertEqual(
            len(at.dataframe), 0, "Dataframe preview should not be rendered after a failure"
        )
