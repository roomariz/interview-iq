"""Community Cloud entrypoint; dependency discovery starts in this directory."""

from interview_app_frontend.app import main
from interview_app_frontend.services.community_cloud import validate_configuration


if __name__ == "__main__":
    import streamlit as st

    try:
        validate_configuration()
    except ValueError as error:
        st.error(str(error))
        st.stop()
    main(demonstration=True)
