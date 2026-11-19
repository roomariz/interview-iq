"""Community Cloud entrypoint; dependency discovery starts in this directory."""

from pathlib import Path
import sys


repository_root = str(Path(__file__).resolve().parents[2])
if repository_root not in sys.path:
    sys.path.insert(0, repository_root)

from interview_app_frontend.app import main  # noqa: E402
from interview_app_frontend.services.community_cloud import validate_configuration  # noqa: E402


if __name__ == "__main__":
    import streamlit as st

    try:
        validate_configuration()
    except ValueError as error:
        st.error(str(error))
        st.stop()
    main(demonstration=True)
