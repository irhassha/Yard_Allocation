import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import matplotlib.colors as mcolors

# Config
st.set_page_config(layout="wide", page_title="Carrier Out per Area")

# --- Upload Data ---
st.sidebar.markdown("## Upload Data Excel")
uploaded_file = st.sidebar.file_uploader(
    "Pilih file .xlsx atau .xls", type=["xlsx","xls"]
)
if not uploaded_file:
    st.sidebar.warning("Silakan upload file Excel terlebih dahulu.")
    st.stop()
try:
    df = pd.read_excel(uploaded_file)
except Exception as e:
    st.sidebar.error(f"Gagal membaca file: {e}")
    st.stop()

# --- Validasi Kolom ---
required = {'Area','Carrier Out','Row_Bay','Move'}
if not required.issubset(df.columns):
    st.error(f"File harus mengandung kolom: {required}")
    st.stop()

# --- Filter Area A01-A08, B01-B08, C01-C08 ---
def in_range(a):
    return isinstance(a,str) and len(a)==3 and a[0] in ['A','B','C'] and a[1:].isdigit() and 1<=int(a[1:])<=8

df = df[df['Area'].apply(in_range)]
if df.empty:
    st.warning("Tidak ada data untuk Area A01–A08, B01–B08, atau C01–C08.")
    st.stop()

# --- Sidebar Filters ---
st.sidebar.markdown("## Filter Move")
move_opts = ['Export','Transhipment','Import']
sel_moves = st.sidebar.multiselect(
    "Tampilkan Move:", options=move_opts, default=['Export','Transhipment']
)

# --- Highlight Carriers ---
# Only carriers in Export & Transhipment
valid_moves = ['Export','Transhipment']
carriers = sorted(df[df['Move'].isin(valid_moves)]['Carrier Out'].unique())
st.sidebar.markdown("## Highlight Carrier Out")
col1, col2 = st.sidebar.columns(2)
if col1.button("Select All"):
    selected = carriers.copy()
elif col2.button("Clear All"):
    selected = []
else:
    selected = st.sidebar.multiselect(
        "Pilih carrier:", options=carriers, default=carriers
    )

# --- Prepare Color Maps ---
palette = list(mcolors.TABLEAU_COLORS.values())
carrier_color_map = {c: palette[i%len(palette)] for i,c in enumerate(carriers)}
gray = '#555555'
yellow = '#FFFF99'

# --- Global Legend ---
st.markdown("### Carrier Out Legend")
legend_fig = go.Figure()
# Import legend entry
legend_fig.add_trace(go.Bar(x=[None], y=[None], name='Import', marker_color=yellow, showlegend=True))
for c in carriers:
    legend_fig.add_trace(go.Bar(x=[None], y=[None], name=c, marker_color=carrier_color_map[c], showlegend=True))
legend_fig.update_layout(
    template='plotly_dark', barmode='stack',
    legend=dict(orientation='h', x=0.5, xanchor='center', y=1.1, yanchor='bottom'),
    margin=dict(t=20, b=0, l=0, r=0), height=60
)
st.plotly_chart(legend_fig, use_container_width=True)

# --- Plot per Area in 3 Columns ---
cols = st.columns(3)
prefixes = ['C','B','A']
for col,prefix in zip(cols,prefixes):
    with col:
        st.markdown(f"**AREA {prefix}**")
        # iterate areas descending
        for area in sorted(df['Area'].unique(), reverse=True):
            if not area.startswith(prefix): continue
            df_area = df[(df['Area']==area) & (df['Move'].isin(sel_moves))]
            # unique per Row_Bay, Carrier Out, Move
            rows = df_area[['Row_Bay','Carrier Out','Move']].drop_duplicates()
            fig = go.Figure()
            used = set()
            # row order descending
            row_order = sorted(rows['Row_Bay'].unique(), reverse=True)
            for rb in row_order:
                sub = rows[rows['Row_Bay']==rb]
                # import segment
                if 'Import' in sel_moves and 'Import' in sub['Move'].values:
                    fig.add_trace(go.Bar(x=[rb], y=[1], name='Import', marker_color=yellow, opacity=1.0, showlegend=False))
                # export/trans carriers
                for c in sub[sub['Move'].isin(valid_moves)]['Carrier Out'].unique():
                    is_sel = c in selected
                    color = carrier_color_map.get(c,gray) if is_sel else gray
                    opacity = 1.0 if is_sel else 0.3
                    showleg = False
                    fig.add_trace(go.Bar(x=[rb], y=[1], name=c, marker_color=color, opacity=opacity, showlegend=False))
            fig.update_layout(
                template='plotly_dark', barmode='stack',
                xaxis=dict(categoryorder='array', categoryarray=row_order, showgrid=False, title=''),
                yaxis=dict(visible=False),
                margin=dict(t=10,b=10,l=0,r=0), height=250
            )
            st.plotly_chart(fig, use_container_width=True)
