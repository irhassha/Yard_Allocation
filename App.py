import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

st.title("📊 Visualisasi Stacked Row/Bay berdasarkan Carrier Out")

uploaded_file = st.file_uploader("Upload File Excel", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    # Rename dan pilih kolom penting
    df = df[['Area (EXE)', 'Move', 'Carrier Out', 'Row/bay (EXE)']]
    df.columns = ['Area', 'Move', 'CarrierOut', 'RowBay']

    # Filter hanya move Export / Transhipment / Import
    df = df[df['Move'].isin(['Export', 'Transhipment', 'Import'])]

    # Pilih Area
    area_selected = st.selectbox("Pilih Area (EXE):", sorted(df['Area'].dropna().unique()))
    area_df = df[df['Area'] == area_selected]

    rowbays = area_df['RowBay'].unique()
    carrier_palette = sns.color_palette("Set2", len(area_df['CarrierOut'].dropna().unique()))
    carrier_colors = dict(zip(area_df['CarrierOut'].dropna().unique(), carrier_palette))

    fig, ax = plt.subplots(figsize=(10, len(rowbays) * 0.6))

    for idx, rowbay in enumerate(sorted(rowbays)):
        group = area_df[area_df['RowBay'] == rowbay]
        grouped = group.groupby(['CarrierOut', 'Move']).size().reset_index(name='Count')

        bottom = 0
        for _, row in grouped.iterrows():
            color = 'lightgrey' if row['Move'] == 'Import' else carrier_colors.get(row['CarrierOut'], 'black')
            ax.barh(rowbay, row['Count'], left=bottom, color=color)
            bottom += row['Count']

    ax.set_title(f"Distribusi Carrier Out per RowBay - Area {area_selected}")
    ax.set_xlabel("Jumlah")
    ax.set_ylabel("Row/Bay")
    st.pyplot(fig)
