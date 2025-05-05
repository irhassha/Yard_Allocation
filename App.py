import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# Judul aplikasi Streamlit
st.title("Visualisasi Data Berdasarkan Carrier Out")

# Instruksi untuk mengunggah file Excel
uploaded_file = st.file_uploader("Unggah file Excel Anda", type=["xlsx"])

if uploaded_file is not None:
    try:
        # Membaca data dari file Excel
        df = pd.read_excel(uploaded_file)

        st.subheader("Data Anda:")
        st.dataframe(df)

        # --- Membuat Visualisasi ---
        st.subheader("Visualisasi Berdasarkan Carrier Out:")

        # Mendapatkan daftar unik dari nilai Carrier Out untuk pewarnaan
        carrier_out_values = df['Carrier Out'].unique()
        color_map = {carrier: f'rgb({i*50 % 256}, {(i+1)*70 % 256}, {(i+2)*90 % 256})'
                     for i, carrier in enumerate(carrier_out_values)}

        # Membuat list untuk menyimpan semua shape (kotak)
        shapes = []
        y_position = 0.8  # Posisi awal y untuk baris pertama
        y_increment = 0.2 # Jarak antar baris visualisasi

        # Membuat list untuk menyimpan anotasi (label Row/bay)
        annotations = []

        for index, row in df.iterrows():
            carrier = row['Carrier Out']
            row_bay = row['Row/bay (EXE)']
            color = color_map.get(carrier, 'lightgray') # Default warna jika Carrier Out tidak dikenali

            # Membuat shape (kotak) untuk setiap baris
            shapes.append(go.layout.Shape(
                type="rect",
                x0=0,
                x1=1, # Lebar visualisasi (bisa disesuaikan)
                y0=y_position - 0.1,
                y1=y_position + 0.1,
                fillcolor=color,
                opacity=0.8,
                line=dict(width=0)
            ))

            # Membuat anotasi untuk label Row/bay
            annotations.append(go.layout.Annotation(
                x=-0.01, # Posisi x label
                y=y_position,
                text=row_bay,
                showarrow=False,
                yshift=0,
                xanchor='right'
            ))

            y_position -= y_increment

        # Membuat layout untuk visualisasi
        layout = go.Layout(
            shapes=shapes,
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[y_position - 0.2, 1]),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-0.1, 1.1]),
            annotations=annotations,
            title="Visualisasi Data Berdasarkan Carrier Out",
            margin=dict(l=100, r=20, t=50, b=20) # Memberikan margin kiri untuk label
        )

        # Membuat figure Plotly
        fig = go.Figure(layout=layout)

        # Menampilkan visualisasi di Streamlit
        st.plotly_chart(fig)

    except Exception as e:
        st.error(f"Terjadi kesalahan: {e}")
else:
    st.info("Silakan unggah file Excel untuk melihat visualisasi.")
