import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# Judul aplikasi Streamlit
st.title("Visualisasi Yard Allocation")

# Instruksi untuk mengunggah file Excel
uploaded_file = st.file_uploader("Unggah file Excel Anda", type=["xlsx"])

if uploaded_file is not None:
    try:
        # Membaca data dari file Excel
        df = pd.read_excel(uploaded_file)

        st.subheader("Data Anda:")
        st.dataframe(df)

        # --- Membuat Visualisasi Layout ---
        st.subheader("Visualisasi Layout:")

        # Filter data untuk Move "Export" dan "Transhipment"
        df_filtered = df[df['Move'].isin(['Export', 'Transhipment'])].copy()
        df_import = df[df['Move'] == 'Import'].copy()

        # Filter hanya blok yang diinginkan
        allowed_blocks = [f'{area}{i:02d}' for area in ['C', 'B', 'A'] for i in range(1, 9)]
        df_filtered = df_filtered[df_filtered['Row/bay (EXE)'].str[:3].isin(allowed_blocks)].copy()
        df_import = df_import[df_import['Row/bay (EXE)'].str[:3].isin(allowed_blocks)].copy()

        # Mendapatkan daftar unik dari nilai Carrier Out untuk pewarnaan
        carrier_out_values = df_filtered['Carrier Out'].unique()
        color_map = {carrier: f'rgb({i*50 % 256}, {(i+1)*70 % 256}, {(i+2)*90 % 256})'
                     for i, carrier in enumerate(carrier_out_values)}
        default_import_color = 'lightgray'

        # Mengelompokkan data berdasarkan 'Row/bay (EXE)' untuk Export/Transhipment
        grouped_data = df_filtered.groupby('Row/bay (EXE)').agg(
            carriers=('Carrier Out', list)
        ).reset_index()
        grouped_data['area'] = grouped_data['Row/bay (EXE)'].str[:1]
        grouped_data['bay'] = grouped_data['Row/bay (EXE)'].str[1:].astype(int) # Convert ke integer untuk sorting

        # Membuat dictionary untuk menyimpan data import per area
        import_data = {}
        for area in ['C', 'B', 'A']:
            import_data[area] = df_import[df_import['Row/bay (EXE)'].str.startswith(area)]['Row/bay (EXE)'].unique()

        # Inisialisasi figure
        fig = go.Figure()

        x_position = 0.15
        x_increment = 0.15
        y_start = 0.9
        y_increment_area = 0.4
        y_increment_stack = 0.15

        annotations = []

        for area_index, area in enumerate(['C', 'B', 'A']):
            area_data = grouped_data[grouped_data['area'] == area].sort_values(by='bay')
            current_y = y_start - (area_index * y_increment_area)
            current_x = x_position

            # Visualisasi untuk Export/Transhipment
            for index, row in area_data.iterrows():
                row_bay = row['Row/bay (EXE)']
                carriers = row['carriers']
                num_carriers = len(carriers)
                y_stack = current_y

                annotations.append(go.layout.Annotation(
                    x=current_x,
                    y=current_y + (y_increment_stack / 2) * (1 - num_carriers),
                    text=row_bay[3:], # Tampilkan hanya nomor bay
                    showarrow=False,
                    xanchor='center',
                    yanchor='middle',
                    font=dict(size=10)
                ))

                for i, carrier in enumerate(carriers):
                    color = color_map.get(carrier, 'lightgray')
                    fig.add_trace(go.Scatter(
                        x=[current_x - 0.05, current_x + 0.05, current_x + 0.05, current_x - 0.05, current_x - 0.05],
                        y=[y_stack - (i * y_increment_stack), y_stack - (i * y_increment_stack),
                           y_stack - ((i + 1) * y_increment_stack), y_stack - ((i + 1) * y_increment_stack),
                           y_stack - (i * y_increment_stack)],
                        fill='toself',
                        fillcolor=color,
                        mode='lines',
                        line=dict(width=0),
                        name=carrier, # Untuk hover info (opsional)
                        showlegend=False
                    ))
                current_x += x_increment

            # Visualisasi untuk Import (di bawah setiap area)
            import_locations_area = sorted([loc[3:] for loc in import_data[area]], key=int)
            if import_locations_area:
                import_y = current_y - y_increment_stack * 1 - 0.05 # Sesuaikan posisi Y
                current_import_x = x_position
                for bay in import_locations_area:
                    fig.add_trace(go.Scatter(
                        x=[current_import_x - 0.05, current_import_x + 0.05, current_import_x + 0.05, current_import_x - 0.05, current_import_x - 0.05],
                        y=[import_y - 0.04, import_y - 0.04, import_y + 0.04, import_y + 0.04, import_y - 0.04],
                        fill='toself',
                        fillcolor=default_import_color,
                        mode='lines',
                        line=dict(width=0),
                        name='Import',
                        showlegend=False
                    ))
                    annotations.append(go.layout.Annotation(
                        x=current_import_x,
                        y=import_y,
                        text=bay,
                        showarrow=False,
                        xanchor='center',
                        yanchor='middle',
                        font=dict(size=10)
                    ))
                    current_import_x += x_increment

            # Label Area
            fig.add_annotation(
                x=0.05,
                y=current_y,
                text=area,
                showarrow=False,
                xanchor='left',
                yanchor='middle',
                font=dict(size=12, weight='bold')
            )

        # Mengatur layout
        fig.update_layout(
            showlegend=True,
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[0, 1]),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[0, 1]),
            shapes=[],
            annotations=annotations,
            title="Visualisasi Yard Allocation Berdasarkan Area dan Row/Bay",
            margin=dict(l=80, r=20, t=50, b=20)
        )

        # Menampilkan visualisasi di Streamlit
        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"Terjadi kesalahan: {e}")
else:
    st.info("Silakan unggah file Excel untuk melihat visualisasi.")
