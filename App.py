import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import matplotlib.colors as mcolors

st.set_page_config(layout="wide", page_title="Carrier Out per Area")

# —————— Upload Excel Data ——————
st.sidebar.markdown("## Upload Data Excel")
uploaded_file = st.sidebar.file_uploader("Pilih file .xlsx atau .xls", type=["xlsx", "xls"])

if not uploaded_file:
    st.sidebar.warning("Silakan upload file Excel terlebih dahulu.")
    st.stop()

# Baca data
try:
    df = pd.read_excel(uploaded_file)
except Exception as e:
    st.sidebar.error(f"Gagal membaca file: {e}")
    st.stop()

# Cek kolom minimum
required_cols = {'Area', 'Carrier Out', 'Row_Bay'}
if not required_cols.issubset(df.columns):
    st.error(f"File harus mengandung kolom: {required_cols}")
    st.stop()

# Filter hanya Area A01-A08, B01-B08, C01-C08
def in_range(area):
    if isinstance(area, str) and len(area) == 3:
        prefix, num = area[0], area[1:]
        return prefix in {'A','B','C'} and num.isdigit() and 1 <= int(num) <= 8
    return False

df = df[df['Area'].apply(in_range)]

# Jika tidak ada data setelah filter
if df.empty:
    st.warning("Tidak ada data untuk Area A01-A08, B01-B08, atau C01-C08 setelah filter.")
    st.stop()

# —————— Setup warna ——————
unique_carriers = df['Carrier Out'].unique().tolist()
palette = list(mcolors.TABLEAU_COLORS.values())
carrier_color_map = {c: palette[i % len(palette)] for i, c in enumerate(unique_carriers)}
gray = '#555555'

# —————— Sidebar: pilih carrier yang di-highlight ——————
st.sidebar.markdown("## Highlight Carrier Out")
selected = st.sidebar.multiselect(
    "Pilih carrier:",
    options=unique_carriers,
    default=unique_carriers
)

# —————— Layout 3 kolom berdasarkan prefix Area ——————
colC, colB, colA = st.columns(3)
groups = {'C': colC, 'B': colB, 'A': colA}

for prefix, col in groups.items():
    with col:
        # Header per kelompok Area (C, B, A)
        st.markdown(f"**AREA {prefix}**", unsafe_allow_html=True)

        # Loop tiap kode Area sesuai prefix
        areas = sorted(df['Area'].unique())
        for area in areas:
            if not isinstance(area, str) or not area.startswith(prefix):
                continue
            df_area = df[df['Area'] == area]
            df_grp = df_area.groupby(['Row_Bay', 'Carrier Out']).size().unstack(fill_value=0)

            fig = go.Figure()
            for carrier in df_grp.columns:
                is_sel = carrier in selected
                fig.add_trace(go.Bar(
                    x=df_grp.index,
                    y=df_grp[carrier],
                    name=carrier,
                    marker_color=carrier_color_map.get(carrier, gray) if is_sel else gray,
                    opacity=1.0 if is_sel else 0.3
                ))

            fig.update_layout(
                barmode='stack',
                template='plotly_dark',
                xaxis=dict(title='', showgrid=False),
                yaxis=dict(title='', showgrid=True, showticklabels=False),
                showlegend=False,
                margin=dict(t=10, b=10, l=10, r=10),
                height=250
            )

            st.plotly_chart(fig, use_container_width=True)
