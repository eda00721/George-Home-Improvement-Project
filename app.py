import json
from io import BytesIO
from pathlib import Path

import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Home Resale Dashboard",
    page_icon="🏠",
    layout="wide"
)

DATA_FILE = Path("home_resale_dashboard_data.json")

STATUS_OPTIONS = ["Not Started", "In Progress", "Completed"]

DEFAULT_DATA = [
    {
        "Objective": "Renovate Kitchen",
        "Description": "New cabinets, paint, and flooring",
        "Status": "Completed",
        "Estimated Cost": 15000.0,
        "Actual Cost": 14500.0,
        "Notes": "Finished on time",
    },
    {
        "Objective": "Landscape Front Yard",
        "Description": "Improve curb appeal",
        "Status": "In Progress",
        "Estimated Cost": 3000.0,
        "Actual Cost": 2000.0,
        "Notes": "Need new mulch",
    },
    {
        "Objective": "Stage House",
        "Description": "Hire staging company",
        "Status": "Not Started",
        "Estimated Cost": 2500.0,
        "Actual Cost": 0.0,
        "Notes": "Scheduled for next week",
    },
]


def load_data() -> pd.DataFrame:
    if DATA_FILE.exists():
        try:
            data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
            df = pd.DataFrame(data)
        except Exception:
            df = pd.DataFrame(DEFAULT_DATA)
    else:
        df = pd.DataFrame(DEFAULT_DATA)

    expected_columns = [
        "Objective",
        "Description",
        "Status",
        "Estimated Cost",
        "Actual Cost",
        "Notes",
    ]

    for col in expected_columns:
        if col not in df.columns:
            df[col] = ""

    df = df[expected_columns].copy()

    for col in ["Estimated Cost", "Actual Cost"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)

    df["Status"] = df["Status"].where(df["Status"].isin(STATUS_OPTIONS), "Not Started")
    df = df.fillna("")
    return df


def save_data(df: pd.DataFrame) -> None:
    clean_df = df.copy().fillna("")
    DATA_FILE.write_text(
        clean_df.to_json(orient="records", indent=2),
        encoding="utf-8"
    )


def build_excel(df: pd.DataFrame) -> bytes:
    output = BytesIO()
    export_df = df.copy()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        export_df.to_excel(writer, index=False, sheet_name="Dashboard")
        ws = writer.book["Dashboard"]

        for cell in ws[1]:
            cell.font = cell.font.copy(bold=True)

        widths = {
            "A": 24,
            "B": 40,
            "C": 16,
            "D": 16,
            "E": 16,
            "F": 40,
        }
        for col_letter, width in widths.items():
            ws.column_dimensions[col_letter].width = width

    output.seek(0)
    return output.getvalue()


def blank_row() -> dict:
    return {
        "Objective": "",
        "Description": "",
        "Status": "Not Started",
        "Estimated Cost": 0.0,
        "Actual Cost": 0.0,
        "Notes": "",
    }


st.title("Home Resale Project Dashboard")
st.caption("Track objectives, descriptions, status, estimated cost, actual cost, and notes.")

if "dashboard_df" not in st.session_state:
    st.session_state.dashboard_df = load_data()

df = st.session_state.dashboard_df.copy()

estimated_total = pd.to_numeric(df["Estimated Cost"], errors="coerce").fillna(0).sum()
actual_total = pd.to_numeric(df["Actual Cost"], errors="coerce").fillna(0).sum()

top1, top2, top3 = st.columns(3)
top1.metric("Total Objectives", len(df))
top2.metric("Estimated Total", f"${estimated_total:,.2f}")
top3.metric("Actual Total", f"${actual_total:,.2f}")

button_col1, button_col2, button_col3, button_col4 = st.columns(4)

with button_col1:
    if st.button("Add Objective", use_container_width=True):
        st.session_state.dashboard_df = pd.concat(
            [st.session_state.dashboard_df, pd.DataFrame([blank_row()])],
            ignore_index=True,
        )
        save_data(st.session_state.dashboard_df)
        st.rerun()

with button_col2:
    if st.button("Save", use_container_width=True):
        save_data(st.session_state.dashboard_df)
        st.success("Dashboard saved.")

with button_col3:
    excel_bytes = build_excel(st.session_state.dashboard_df)
    st.download_button(
        "Download Excel",
        data=excel_bytes,
        file_name="home_resale_dashboard_data.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )

with button_col4:
    if st.button("Reset to Default", use_container_width=True):
        st.session_state.dashboard_df = pd.DataFrame(DEFAULT_DATA)
        save_data(st.session_state.dashboard_df)
        st.rerun()

edited_df = st.data_editor(
    st.session_state.dashboard_df,
    num_rows="dynamic",
    use_container_width=True,
    hide_index=True,
    column_config={
        "Objective": st.column_config.TextColumn("Objective", width="medium"),
        "Description": st.column_config.TextColumn("Description", width="large"),
        "Status": st.column_config.SelectboxColumn("Status", options=STATUS_OPTIONS, width="small"),
        "Estimated Cost": st.column_config.NumberColumn("Estimated Cost", format="%.2f"),
        "Actual Cost": st.column_config.NumberColumn("Actual Cost", format="%.2f"),
        "Notes": st.column_config.TextColumn("Notes", width="large"),
    },
)

for col in ["Estimated Cost", "Actual Cost"]:
    edited_df[col] = pd.to_numeric(edited_df[col], errors="coerce").fillna(0.0)
edited_df["Status"] = edited_df["Status"].where(edited_df["Status"].isin(STATUS_OPTIONS), "Not Started")

st.session_state.dashboard_df = edited_df
save_data(edited_df)

with st.expander("How this app saves your data"):
    st.write(
        "This app saves dashboard data to a local JSON file named "
        "`home_resale_dashboard_data.json` in the same folder as the app. "
        "Use Download Excel anytime for a formatted spreadsheet export."
    )
