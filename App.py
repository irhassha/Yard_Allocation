import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# Judul aplikasi Streamlit
st.title("Visualisasi Detail Berdasarkan Carrier Out dan Move")

# Instruksi untuk mengunggah file Excel
uploaded_file = st.file_uploader("Unggah file Excel Anda", type=["xlsx"])

if uploaded_file is not None:
    try:
        # Membaca data dari file Excel
        df = pd.read_excel(uploaded_file)

        st.subheader("Data Anda:")
        st.dataframe(df)

        # --- Membuat Visualisasi Detail ---
        st.subheader("Visualisasi Detail:")

        # Filter data untuk Move "Export" dan "Transhipment" untuk pewarnaan
        df_filtered = df[df['Move'].isin(['Export', 'Transhipment'])].copy()
        df_import = df[df['Move'] == 'Import'].copy()

        # Mendapatkan daftar unik dari nilai Carrier Out untuk pewarnaan
        carrier_out_values = df_filtered['Carrier Out'].unique()
        color_map = {carrier: f'rgb({i*50 % 256}, {(i+1)*70 % 256}, {(i+2)*90 % 256})'
                     for i, carrier in enumerate(carrier_out_values)}
        default_import_color = 'lightgray'

        # Mengelompokkan data berdasarkan 'Row/bay (EXE)'
        grouped_data = df_filtered.groupby('Row/bay (EXE)').agg(
            carriers=('Carrier Out', list),
            moves=('Move', list)
        ).reset_index()

        import_locations = df_import['Row/bay (EXE)'].unique()

        # Inisialisasi figure
        fig = go.Figure()

        y_position = 0.95
        y_increment = 0.3
        x_start = 0
        x_width = 0.2
        x_increment = 0.25

        annotations = []

        # Membuat visualisasi untuk data Export dan Transhipment
        for index, row in grouped_data.iterrows():
            row_bay = row['Row/bay (EXE)']
            carriers = row['carriers']
            moves = row['moves']
            num_carriers = len(carriers)
            y_stack_start = y_position

            annotations.append(go.layout.Annotation(
                x=x_start - 0.01,
                y=y_position - (y_increment / 2),
                text=row_bay,
                showarrow=False,
                yshift=0,
                xanchor='right'
            ))

            for i, carrier in enumerate(carriers):
                color = color_map.get(carrier, 'lightgray')
                height = y_increment / num_carriers

                fig.add_trace(go.Scatter(
                    x=[x_start, x_start + x_width, x_start + x_width, x_start, x_start],
                    y=[y_stack_start - (i * height), y_stack_start - (i * height),
                       y_stack_start - ((i + 1) * height), y_stack_start - ((i + 1) * height),
                       y_stack_start - (i * height)],
                    fill='toself',
                    fillcolor=color,
                    mode='lines',
                    line=dict(width=0),
                    name=carrier # Untuk hover info (opsional)
                ))

            x_start += x_increment
            if (index + 1) % 4 == 0: # Untuk membuat baris baru setelah 4 Row/bay
                x_start = 0
                y_position -= y_increment * 1.5 # Tambah jarak antar kelompok baris

        # Membuat visualisasi untuk data Import (warna abu-abu)
        for location in import_locations:
            fig.add_trace(go.Scatter(
                x=[0, x_width, x_width, 0, 0],
                y=[y_position - (y_increment / 2) - 0.1, y_position - (y_increment / 2) - 0.1,
                   y_position - (y_increment / 2) + 0.1, y_position - (y_increment / 2) + 0.1,
                   y_position - (y_increment / 2) - 0.1],
                fill='toself',
                fillcolor=default_import_color,
                mode='lines',
                line=dict(width=0),
                name='Import' # Untuk hover info (opsional)
            ))
            annotations.append(go.layout.Annotation(
                x=-0.01,
                y=y_position - (y_increment / 2),
                text=location,
                showarrow=False,
                yshift=0,
                xanchor='right'
            ))
            # Kita perlu mekanisme penempatan yang lebih baik untuk import,
            # karena lokasinya mungkin tumpang tindih dengan export/transhipment.
            # Untuk saat ini, kita akan menempatkannya di baris yang sama,
            # tapi ini perlu disesuaikan berdasarkan data Anda.

        # Mengatur layout
        fig.update_layout(
            showlegend=True,
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-0.1, x_start + x_width + 0.1]),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[y_position - y_increment * 2, 1]),
            shapes=[], # Shapes akan ditambahkan melalui trace
            annotations=annotations,
            title="Visualisasi Detail Berdasarkan Carrier Out dan Move",
            margin=dict(l=120, r=20, t=50, b=20)
        )

        # Menampilkan visualisasi di Streamlit
        st.plotly_chart(fig)

    except Exception as e:
        st.error(f"Terjadi kesalahan: {e}")
else:
    st.info("Silakan unggah file Excel untuk melihat visualisasi.")
