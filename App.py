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

    # Drop baris tanpa Row/bay
    df = df.dropna(subset=["Row/bay (EXE)"])

    # Filter hanya Move yang kita pedulikan
    df = df[df["Move"].isin(["Export", "Transhipment", "Import"])]

    # Buat list RowBay dan pasangan (Move, Carrier)
    rowbay_map = defaultdict(list)
    for _, row in df.iterrows():
        rowbay = row["Row/bay (EXE)"]
        move = row["Move"]
        carrier = str(row["Carrier Out"]) if pd.notna(row["Carrier Out"]) else "UNKNOWN"
        rowbay_map[rowbay].append((move, carrier))

    sorted_rowbays = sorted(rowbay_map.keys())

    # Siapkan color map hanya untuk Export & Transhipment
    export_carriers = df[df["Move"].isin(["Export", "Transhipment"])]["Carrier Out"].dropna().unique()
    colors = plt.cm.tab20.colors
    color_map = {str(carrier): colors[i % len(colors)] for i, carrier in enumerate(export_carriers)}

    # Slider jumlah Row/Bay yang ditampilkan
    max_display = st.slider("Jumlah Row/Bay yang ditampilkan", min_value=10, max_value=len(sorted_rowbays), value=50)
    displayed_rowbays = sorted_rowbays[:max_display]

    # Ukuran figure fleksibel
    fig_width = min(20, len(displayed_rowbays))
    fig_height = 6
    fig, ax = plt.subplots(figsize=(fig_width, fig_height))

    for i, rowbay in enumerate(displayed_rowbays):
        entries = rowbay_map[rowbay]
        unique_entries = list(dict.fromkeys(entries))  # hapus duplikat

        for j, (move, carrier) in enumerate(unique_entries):
            if move == "Import":
                color = "#BBBBBB"  # abu-abu
            else:
                color = color_map.get(carrier, "#BBBBBB")

            ax.add_patch(plt.Rectangle((i, j), 1, 1, color=color))

        ax.text(i + 0.5, -0.5, rowbay, ha='center', va='top', fontsize=8, rotation=90)

    ax.set_xlim(0, len(displayed_rowbays))
    ax.set_ylim(0, max(len(v) for v in rowbay_map.values()) + 1)
    ax.axis("off")

    # Buat legend
    legend_handles = [mpatches.Patch(color=color_map[c], label=c) for c in color_map]
    legend_handles.append(mpatches.Patch(color="#BBBBBB", label="Import / Unknown"))
    ax.legend(handles=legend_handles, bbox_to_anchor=(1.05, 1), loc='upper left', title="Carrier Out")

    st.pyplot(fig)
