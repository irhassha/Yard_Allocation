import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Load data
uploaded_file = st.file_uploader("Upload CSV File", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)

    # Hanya ambil kolom penting
    df = df[['Area (EXE)', 'Move', 'Carrier Out', 'Row/bay (EXE)']]
    df.columns = ['Area', 'Move', 'CarrierOut', 'RowBay']

    # Filter Move
    df = df[df['Move'].isin(['Export', 'Transhipment']) | df['Move'] == 'Import']

    # Area selector
    area_selected = st.selectbox("Pilih Area:", sorted(df['Area'].dropna().unique()))

    area_df = df[df['Area'] == area_selected]

    # Plot per RowBay
    rowbays = area_df['RowBay'].unique()

    # Warna carrier dinamis
    carrier_palette = sns.color_palette("hls", len(area_df['CarrierOut'].dropna().unique()))
    carrier_colors = dict(zip(area_df['CarrierOut'].dropna().unique(), carrier_palette))

    fig, ax = plt.subplots(figsize=(10, len(rowbays)*0.6))

    for idx, rowbay in enumerate(sorted(rowbays)):
        group = area_df[area_df['RowBay'] == rowbay]
        move_counts = group.groupby(['CarrierOut', 'Move']).size().reset_index(name='Count')

        bottom = 0
        for _, row in move_counts.iterrows():
            color = 'grey' if row['Move'] == 'Import' else carrier_colors.get(row['CarrierOut'], 'black')
            ax.barh(rowbay, row['Count'], left=bottom, color=color)
            bottom += row['Count']

    ax.set_title(f"Distribusi Carrier Out per RowBay - Area {area_selected}")
    ax.set_xlabel("Jumlah")
    st.pyplot(fig)
