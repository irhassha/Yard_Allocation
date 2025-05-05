import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

st.title("📦 Visualisasi Row/Bay per Area (EXE) - Horizontal Layout")

uploaded_file = st.file_uploader("Upload File Excel", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    # Bersihkan dan rename kolom
    df = df[['Area (EXE)', 'Move', 'Carrier Out', 'Row/bay (EXE)']]
    df.columns = ['Area', 'Move', 'CarrierOut', 'RowBay']

    # Filter hanya Move yang diperlukan
    df = df[df['Move'].isin(['Export', 'Transhipment', 'Import'])]

    # Buat palette warna CarrierOut (selain Import)
    unique_carriers = df[df['Move'] != 'Import']['CarrierOut'].dropna().unique()
    carrier_palette = sns.color_palette("tab10", len(unique_carriers))
    carrier_colors = dict(zip(unique_carriers, carrier_palette))

    # Warna untuk Import
    import_color = 'lightgrey'

    # Loop setiap Area
    for area in sorted(df['Area'].dropna().unique()):
        st.subheader(f"📍 Area: {area}")
        area_df = df[df['Area'] == area]

        rowbays = sorted(area_df['RowBay'].dropna().unique())
        fig, ax = plt.subplots(figsize=(len(rowbays), 4))

        # Posisi stack tiap RowBay
        for i, rowbay in enumerate(rowbays):
            stack = area_df[area_df['RowBay'] == rowbay]
            stack = stack.groupby(['CarrierOut', 'Move']).size().reset_index(name='Count')

            bottom = 0
            for _, row in stack.iterrows():
                color = import_color if row['Move'] == 'Import' else carrier_colors.get(row['CarrierOut'], 'black')
                ax.bar(i, row['Count'], bottom=bottom, color=color, edgecolor='black')
                bottom += row['Count']

        ax.set_xticks(range(len(rowbays)))
        ax.set_xticklabels(rowbays, rotation=90)
        ax.set_ylabel("Jumlah")
        ax.set_title(f"Distribusi per Row/Bay - Area {area}")
        st.pyplot(fig)
