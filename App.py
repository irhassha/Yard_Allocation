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

    # Clean header if needed
    df.columns = df.columns.str.strip()

    # Drop rows with missing Row/Bay
    df = df.dropna(subset=["Row/bay (EXE)"])

    # Grouping by Row/Bay dan Carrier
    rowbay_carriers = df.groupby("Row/bay (EXE)")["Carrier Out"].apply(list)

    # Get unique Row/Bay and sorting (opsional)
    sorted_rowbays = sorted(rowbay_carriers.index.tolist())

    # Assign unique colors to each carrier
    all_carriers = df["Carrier Out"].dropna().unique()
    colors = plt.cm.tab20.colors
    color_map = {carrier: colors[i % len(colors)] for i, carrier in enumerate(all_carriers)}

    fig, ax = plt.subplots(figsize=(len(sorted_rowbays), 5))

    for i, rowbay in enumerate(displayed_rowbays):
    entries = rowbay_map[rowbay]
    
    # Remove duplicate (move, carrier) pair
    unique_entries = list(dict.fromkeys(entries))

    for j, (move, carrier) in enumerate(unique_entries):
        if move == "Import":
            color = "#BBBBBB"  # abu-abu
        else:
            color = color_map.get(carrier, "#BBBBBB")

        ax.add_patch(plt.Rectangle((i, j), 1, 1, color=color))

    ax.text(i + 0.5, -0.5, rowbay, ha='center', va='top', fontsize=8, rotation=90)



    ax.set_xlim(0, len(sorted_rowbays))
    ax.set_ylim(0, max(len(set(c)) for c in rowbay_carriers) + 1)
    ax.axis("off")

    # Legend
    legend_handles = [mpatches.Patch(color=color_map[c], label=c) for c in color_map]
    ax.legend(handles=legend_handles, bbox_to_anchor=(1.05, 1), loc='upper left', title="Carrier Out")

    st.pyplot(fig)
