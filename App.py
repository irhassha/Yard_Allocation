import streamlit as st
import pandas as pd
import plotly.express as px
import matplotlib.colors as mcolors

# Config
st.set_page_config(layout="wide", page_title="Carrier Out per Area")

# --- Upload Data ---
st.sidebar.markdown("## Upload Data Excel")
uploaded_file = st.sidebar.file_uploader("Pilih file .xlsx atau .xls", type=["xlsx","xls"])
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
    st.warning("Tidak ada data untuk Area A01–A08, B01–B08, C01–C08.")
    st.stop()

# --- Sidebar Filters ---
st.sidebar.markdown("## Filter Move")
move_opts = ['Export','Transhipment','Import']
sel_moves = st.sidebar.multiselect("Tampilkan Move:", options=move_opts, default=['Export','Transhipment'])

# --- Prepare data for visualization ---
df_vis = df[df['Move'].isin(sel_moves)][['Area','Row_Bay','Carrier Out','Move']].drop_duplicates()
# create a unified category for legend

df_vis['Carrier_Vis'] = df_vis.apply(lambda r: 'Import' if r['Move']=='Import' else r['Carrier Out'], axis=1)

# --- Setup colors ---
palette = list(mcolors.TABLEAU_COLORS.values())
carriers = sorted(df_vis['Carrier_Vis'].unique())
# assign Import to yellow
color_map = {c: palette[i%len(palette)] for i,c in enumerate(carriers) if c!='Import'}
if 'Import' in carriers:
    color_map['Import'] = '#FFFF99'

# --- Ordering ---
area_order = sorted(df_vis['Area'].unique(), reverse=True)
row_order = sorted(df_vis['Row_Bay'].unique(), reverse=True)

df_vis['Count'] = 1

# --- Plot facets with Plotly Express ---
fig = px.bar(
    df_vis,
    x='Row_Bay', y='Count', color='Carrier_Vis',
    facet_col='Area', facet_col_wrap=3,
    category_orders={'Area':area_order, 'Row_Bay':row_order},
    color_discrete_map=color_map,
    height=350 * ((len(area_order)+2)//3)
)
# layout adjustments
fig.update_layout(
    barmode='stack', template='plotly_dark',
    legend=dict(orientation='h', x=0.5, xanchor='center', y=1.1, yanchor='bottom'),
    margin=dict(t=60, b=40)
)
# hide y axes
fig.update_yaxes(visible=False)
# rotate x ticks
fig.update_xaxes(tickangle=-45)

st.plotly_chart(fig, use_container_width=True)
