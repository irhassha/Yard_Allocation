import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from collections import defaultdict

st.set_page_config(layout="wide")
st.title("📦 Visualisasi Row/Bay berdasarkan Carrier Out")

uploaded_file = st.file_uploader("Upload file Excel kamu", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    df.columns = df.columns.str.strip()

    df = df.dropna(subset=["Row/bay (EXE)"])
    df = df[df["Move"].isin(["Export", "Transhipment", "Import"])]

    # Filter Area
    if "Area (EXE)" in df.columns:
        available_areas = df["Area (EXE)"].dropna().unique()
        selected_areas = st.multiselect("Pilih Area yang ingin ditampilkan", options=sorted(available_areas), default=sorted(available_areas))
        df = df[df["Area (EXE)"].isin(selected_areas)]

    # Buat mapping data
    rowbay_map = defaultdict(list)
    for _, row in df.iterrows():
        rowbay = row["Row/bay (EXE)"]
        move = row["Move"]
        carrier = str(row["Carrier Out"]) if pd.notna(row["Carrier Out"]) else "UNKNOWN"
        rowbay_map[rowbay].append((move, carrier))

    # Buat grid A01–C08
    rows = [f"{i:02}" for i in range(1, 9)]
    cols = ["A", "B", "C"]
    grid_order = [f"{col}{row}" for row in reversed(rows) for col in reversed(cols)]  # C08 → A01
    displayed_rowbays = [rb for rb in grid_order if rb in rowbay_map]

    # Warnain hanya Export & Transhipment
    export_carriers = df[df["Move"].isin(["Export", "Transhipment"])]["Carrier Out"].dropna().unique()
    colors = plt.cm.tab20.colors
    color_map = {str(carrier): colors[i % len(colors)] for i, carrier in enumerate(export_carriers)}

    fig, ax = plt.subplots(figsize=(8, 10))

    for rowbay in displayed_rowbays:
        col_letter = rowbay[0]
        row_number = rowbay[1:]
        col = {"A": 0, "B": 1, "C": 2}[col_letter]
        row = 8 - int(row_number)

        entries = rowbay_map[rowbay]
        unique_entries = list(dict.fromkeys(entries))

        for j, (move, carrier) in enumerate(unique_entries):
            color = "#BBBBBB" if move == "Import" else color_map.get(carrier, "#BBBBBB")
            ax.add_patch(plt.Rectangle((col, row - j * 0.2), 1, 0.2, color=color))

        ax.text(col + 0.5, row - 0.5, rowbay, ha='center', va='top', fontsize=8)

    ax.set_xlim(0, 3)
    ax.set_ylim(-0.5, 8)
    ax.set_xticks(range(3))
    ax.set_xticklabels(["A", "B", "C"])
    ax.set_yticks(range(8))
    ax.set_yticklabels(list(reversed([f"{i:02}" for i in range(1, 9)])))
    ax.invert_yaxis()
    ax.grid(True)

    # Legend
    legend_handles = [mpatches.Patch(color=color_map[c], label=c) for c in color_map]
    legend_handles.append(mpatches.Patch(color="#BBBBBB", label="Import / Unknown"))
    ax.legend(handles=legend_handles, bbox_to_anchor=(1.05, 1), loc='upper left', title="Carrier Out")

    st.pyplot(fig)
