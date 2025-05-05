import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from collections import defaultdict

st.set_page_config(layout="wide")
st.title("📦 Visualisasi Row/Bay per Carrier Out")

uploaded_file = st.file_uploader("Upload file Excel kamu", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    df.columns = df.columns.str.strip()

    df = df.dropna(subset=["Row/bay (EXE)"])
    df = df[df["Move"].isin(["Export", "Transhipment", "Import"])]

    if "Area (EXE)" not in df.columns:
        st.error("Kolom 'Area (EXE)' tidak ditemukan di file.")
        st.stop()

    available_areas = df["Area (EXE)"].dropna().unique()
    selected_areas = st.multiselect("Pilih Area yang ingin ditampilkan", options=sorted(available_areas), default=sorted(available_areas))

    export_carriers = df[df["Move"].isin(["Export", "Transhipment"])]["Carrier Out"].dropna().unique()
    colors = plt.cm.tab20.colors
    color_map = {str(carrier): colors[i % len(colors)] for i, carrier in enumerate(export_carriers)}

    for area in selected_areas:
        st.subheader(f"Area: {area}")
        df_area = df[df["Area (EXE)"] == area]

        rowbay_map = defaultdict(list)
        for _, row in df_area.iterrows():
            rowbay = str(row["Row/bay (EXE)"])
            move = row["Move"]
            carrier = str(row["Carrier Out"]) if pd.notna(row["Carrier Out"]) else "UNKNOWN"
            rowbay_map[rowbay].append((move, carrier))

        # Buat list unik Row/Bay dari data (diurutkan secara logis)
        all_rowbays = list(rowbay_map.keys())
        bay_ids = sorted(set(rb.split("-")[0] for rb in all_rowbays))
        col_ids = sorted(set(rb.split("-")[1] for rb in all_rowbays), key=lambda x: int(x))

        n_rows = len(bay_ids)
        n_cols = len(col_ids)

        fig, ax = plt.subplots(figsize=(n_cols * 1.1, n_rows * 1))

        for y, bay in enumerate(bay_ids):
            for x, col in enumerate(col_ids):
                full_id = f"{bay}-{col}"
                entries = rowbay_map.get(full_id, [])
                entries = list(dict.fromkeys(entries))  # Hapus duplikat

                # Stack warna ke atas jika lebih dari satu
                for i, (move, carrier) in enumerate(reversed(entries)):
                    color = "#BBBBBB" if move == "Import" else color_map.get(carrier, "#BBBBBB")
                    ax.add_patch(plt.Rectangle((x, y + i * 0.2), 1, 0.2, color=color))

                # Border kotak
                ax.add_patch(plt.Rectangle((x, y), 1, 1, fill=False, edgecolor='black'))

                # Label RowBay
                if entries:
                    ax.text(x + 0.5, y + 0.5, full_id, ha="center", va="center", fontsize=7)

        ax.set_xlim(0, n_cols)
        ax.set_ylim(0, n_rows + 1)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.invert_yaxis()
        ax.set_aspect('equal')

        # Legend
        legend_handles = [mpatches.Patch(color=color_map[c], label=c) for c in color_map]
        legend_handles.append(mpatches.Patch(color="#BBBBBB", label="Import / Unknown"))
        ax.legend(handles=legend_handles, bbox_to_anchor=(1.05, 1), loc='upper left', title="Carrier Out")

        st.pyplot(fig)
