from __future__ import annotations

import streamlit as st

from src.ui.pages import render_app
from src.ui.state import init_state


def main() -> None:
    st.set_page_config(page_title="OpenDrift PlastDrift 표층 연구", layout="wide")
    init_state()
    render_app()


if __name__ == "__main__":
    main()
