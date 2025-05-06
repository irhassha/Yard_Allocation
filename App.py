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
required_cols = {'Area', 'Carrier Out', 'Row_Bay', 'Move'}
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
yellow = '#FFFF99'  # untuk Import

# —————— Sidebar: pilih carrier highlight ——————
st.sidebar.markdown("## Highlight Carrier Out")
selected = st.sidebar.multiselect(
    "Pilih carrier:",
    options=unique_carriers,
    default=unique_carriers
)

# —————— Layout 3 kolom per prefix Area ——————
colC, colB, colA = st.columns(3)
groups = {'C': colC, 'B': colB, 'A': colA}

for prefix, col in groups.items():
    with col:
        st.markdown(f"**AREA {prefix}**", unsafe_allow_html=True)
        areas = sorted(df['Area'].unique())
        for area in areas:
            if not area.startswith(prefix):
                continue
            df_area = df[df['Area'] == area]
            # group by Row_Bay, Carrier Out, Move
            grp = df_area.groupby(['Row_Bay','Carrier Out','Move']).size().reset_index(name='count')

            fig = go.Figure()
            seen_legend = set()
            for _, r in grp.iterrows():
                rb, carrier, move, cnt = r['Row_Bay'], r['Carrier Out'], r['Move'], r['count']
                if cnt <= 0:
                    continue
                # tentukan warna dan opacity
                if move == 'Import':
                    color = yellow
                    opacity = 1.0
                    showleg = False
                else:
                    color = carrier_color_map.get(carrier, gray) if carrier in selected else gray
                    opacity = 1.0 if carrier in selected else 0.3
                    showleg = (carrier not in seen_legend)
                    if showleg:
                        seen_legend.add(carrier)
                fig.add_trace(go.Bar(
                    x=[rb],
                    y=[cnt],
                    name=carrier,
                    marker_color=color,
                    opacity=opacity,
                    showlegend=showleg
                ))

            fig.update_layout(
                barmode='stack',
                template='plotly_dark',
                xaxis=dict(title='', showgrid=False),
                yaxis=dict(title='', showgrid=True, showticklabels=False),
                legend_title='Carrier Out',
                margin=dict(t=10, b=10, l=10, r=10),
                height=250
            )

            # tampilkan chart
            st.plotly_chart(fig, use_container_width=True)
