import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import matplotlib.colors as mcolors

st.set_page_config(layout="wide", page_title="Carrier Out per Area")

# —————— Upload Excel Data ——————
st.sidebar.markdown("## Upload Data Excel")
uploaded_file = st.sidebar.file_uploader(
    "Pilih file .xlsx atau .xls", type=["xlsx", "xls"]
)
if not uploaded_file:
    st.sidebar.warning("Silakan upload file Excel terlebih dahulu.")
    st.stop()

# —————— Baca data ——————
try:
    df = pd.read_excel(uploaded_file)
except Exception as e:
    st.sidebar.error(f"Gagal membaca file: {e}")
    st.stop()

# —————— Validasi kolom ——————
required_cols = {'Area', 'Carrier Out', 'Row_Bay', 'Move'}
if not required_cols.issubset(df.columns):
    st.error(f"File harus memiliki kolom: {required_cols}")
    st.stop()

# —————— Filter Area A01-A08, B01-B08, C01-C08 ——————
def in_range(area):
    if isinstance(area, str) and len(area) == 3:
        prefix, num = area[0], area[1:]
        return prefix in {'A', 'B', 'C'} and num.isdigit() and 1 <= int(num) <= 8
    return False

df = df[df['Area'].apply(in_range)]
if df.empty:
    st.warning("Tidak ada data untuk Area A01-A08, B01-B08, atau C01-C08 setelah filter.")
    st.stop()

# —————— Setup warna ——————
all_carriers = df['Carrier Out'].unique().tolist()
palette = list(mcolors.TABLEAU_COLORS.values())
carrier_color_map = {c: palette[i % len(palette)] for i, c in enumerate(all_carriers)}
gray = '#555555'
yellow = '#FFFF99'  # Warna untuk Import

# —————— Sidebar: Pilih Move ——————
st.sidebar.markdown("## Filter Move")
move_options = ['Export', 'Transhipment', 'Import']
selected_moves = st.sidebar.multiselect(
    "Tampilkan Move:", options=move_options, default=['Export', 'Transhipment']
)

# —————— Sidebar: Pilih Carrier (Export & Transhipment) ——————
valid_moves = ['Export', 'Transhipment']
export_trans_carriers = sorted(df[df['Move'].isin(valid_moves)]['Carrier Out'].unique())
st.sidebar.markdown("## Highlight Carrier Out")
col_sa, col_ca = st.sidebar.columns(2)
if col_sa.button("Select All"):
    selected = export_trans_carriers.copy()
elif col_ca.button("Clear All"):
    selected = []
else:
    selected = st.sidebar.multiselect(
        "Pilih carrier (Export & Transhipment saja):",
        options=export_trans_carriers,
        default=export_trans_carriers
    )

# —————— Tampilkan Legend Global di atas ——————
# Buat figure kosong hanya untuk legend
legend_fig = go.Figure()
for carrier in export_trans_carriers:
    color = carrier_color_map.get(carrier, gray)
    legend_fig.add_trace(go.Bar(
        x=[None], y=[None], name=carrier,
        marker_color=color,
        showlegend=True
    ))
legend_fig.update_layout(
    template='plotly_dark',
    legend_title='Carrier Out',
    showlegend=True,
    legend=dict(
        orientation='h',
        yanchor='bottom',
        y=1.02,
        xanchor='center',
        x=0.5
    ),
    height=80,
    margin=dict(t=10, b=10, l=10, r=10)
)
)
st.plotly_chart(legend_fig, use_container_width=True)

# —————— Layout 3 kolom per prefix Area ——————
cols = st.columns(3)
prefixes = ['C', 'B', 'A']
for col, prefix in zip(cols, prefixes):
    with col:
        st.markdown(f"**AREA {prefix}**")
        for area in sorted(df['Area'].unique(), reverse=True):
            if not area.startswith(prefix):
                continue
            df_area = df[(df['Area'] == area) & (df['Move'].isin(selected_moves))]
            unique_rows = df_area[['Row_Bay', 'Carrier Out', 'Move']].drop_duplicates()
            fig = go.Figure()
            used = set()
            row_bays = sorted(unique_rows['Row_Bay'].unique(), reverse=True)
            for rb in row_bays:
                subset = unique_rows[unique_rows['Row_Bay'] == rb]
                has_imp = 'Import' in selected_moves and 'Import' in subset['Move'].values
                carriers = subset[subset['Move'].isin(valid_moves)]['Carrier Out'].unique().tolist()
                # Uniform height
                h = 1
                if has_imp:
                    fig.add_trace(go.Bar(
                        x=[rb], y=[h], name='Import',
                        marker_color=yellow, opacity=1.0,
                        showlegend=False
                    ))
                for carrier in carriers:
                    is_sel = carrier in selected
                    color = carrier_color_map.get(carrier, gray) if is_sel else gray
                    opacity = 1.0 if is_sel else 0.3
                    # legend hanya global, disable per-area
                    fig.add_trace(go.Bar(
                        x=[rb], y=[h], name=carrier,
                        marker_color=color, opacity=opacity,
                        showlegend=False
                    ))
            fig.update_layout(
                barmode='stack',
                template='plotly_dark',
                xaxis=dict(
                    title='', showgrid=False,
                    categoryorder='array', categoryarray=row_bays
                ),
                yaxis=dict(title='', showgrid=False, showticklabels=False),
                margin=dict(t=10, b=10, l=10, r=10),
                height=260
            )
            st.plotly_chart(fig, use_container_width=True)
