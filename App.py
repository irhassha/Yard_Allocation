import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import matplotlib.colors as mcolors

# Halaman
st.set_page_config(layout="wide", page_title="Carrier Out per Area")

# --- Sidebar: Upload Data ---
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

# Validasi kolom
required_cols = {'Area', 'Carrier Out', 'Row_Bay', 'Move'}
if not required_cols.issubset(df.columns):
    st.error(f"File harus mengandung kolom: {required_cols}")
    st.stop()

# Filter hanya Area A01-A08, B01-B08, C01-C08
def in_range(a):
    return isinstance(a, str) and len(a)==3 and a[0] in ['A','B','C'] and a[1:].isdigit() and 1<=int(a[1:])<=8

df = df[df['Area'].apply(in_range)]
if df.empty:
    st.warning("Tidak ada data untuk Area A01–A08, B01–B08, atau C01–C08.")
    st.stop()

# --- Sidebar: Filter Move ---
st.sidebar.markdown("## Filter Move")
move_opts = ['Export', 'Transhipment', 'Import']
sel_moves = st.sidebar.multiselect(
    "Tampilkan Move:", options=move_opts, default=['Export','Transhipment']
)

# --- Sidebar: Highlight Carrier ---
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

# --- Color maps ---
palette = list(mcolors.TABLEAU_COLORS.values())
carrier_color_map = {c: palette[i%len(palette)] for i,c in enumerate(carriers)}
gray = '#555555'
yellow = '#FFFF99'

# --- Tabs: Dashboard & Fitur Lain ---
tab1, tab2 = st.tabs(["Dashboard", "Plan Capacity Calculator"])

with tab1:
    # Global Legend
    st.markdown("### Carrier Out Legend")
    legend_fig = go.Figure()
    # Import entry
    legend_fig.add_trace(go.Bar(x=[None], y=[None], name='Import', marker_color=yellow, showlegend=True))
    # Export/Tranship entries
    for c in carriers:
        legend_fig.add_trace(go.Bar(x=[None], y=[None], name=c, marker_color=carrier_color_map[c], showlegend=True))
    legend_fig.update_layout(
        template='plotly_dark', barmode='stack',
        legend=dict(orientation='h', x=0.5, y=1.1, xanchor='center', yanchor='bottom'),
        margin=dict(t=20,b=0,l=0,r=0), height=60
    )
    st.plotly_chart(legend_fig, use_container_width=True, key='legend_fig')

    # Plot per Area
    cols = st.columns(3)
    prefixes = ['C','B','A']
    for col,prefix in zip(cols,prefixes):
        with col:
            st.markdown(f"**AREA {prefix}**")
            for area in sorted(df['Area'].unique(), reverse=True):
                if not area.startswith(prefix): continue
                df_area = df[(df['Area']==area) & (df['Move'].isin(sel_moves))]
                rows = df_area[['Row_Bay','Carrier Out','Move']].drop_duplicates()
                fig = go.Figure()
                # Order Row_Bay descending
                row_order = sorted(rows['Row_Bay'].unique(), reverse=True)
                for rb in row_order:
                    sub = rows[rows['Row_Bay']==rb]
                    # Import segment
                    if 'Import' in sel_moves and 'Import' in sub['Move'].values:
                        fig.add_trace(go.Bar(
                            x=[rb], y=[1], name='Import', marker_color=yellow,
                            opacity=1.0, showlegend=False
                        ))
                    # Export/Tranship segments
                    for c in sub[sub['Move'].isin(valid_moves)]['Carrier Out'].unique():
                        is_sel = c in selected
                        color = carrier_color_map[c] if is_sel else gray
                        opacity = 1.0 if is_sel else 0.3
                        fig.add_trace(go.Bar(
                            x=[rb], y=[1], name=c, marker_color=color,
                            opacity=opacity, showlegend=False
                        ))
                fig.update_layout(
                    template='plotly_dark', barmode='stack',
                    xaxis=dict(categoryorder='array', categoryarray=row_order, showgrid=False, title=''),
                    yaxis=dict(visible=False), margin=dict(t=10,b=10,l=0,r=0), height=250
                )
                st.plotly_chart(fig, use_container_width=True, key=f"chart_{prefix}_{area}")

with tab2:
    st.header("Plan Capacity Calculator")
    # Input dynamic rows
    df_input = pd.DataFrame(columns=["Area","Slot","Height"])
    edited = st.data_editor(df_input, num_rows="dynamic", use_container_width=True, key='editor')

    # Kalkulasi untuk setiap input
multiplier = 6
plan_rows = []
for _, row in edited.iterrows():
    area_text = (row.get("Area") or "").strip()
    slot_text = (row.get("Slot") or "").strip()
    # Parsing Height
    try:
        height = int(float(row.get("Height", 0)))
    except:
        height = 0
    # List area
    area_list = [a.strip() for a in area_text.split(',') if a.strip()]
    num_areas = len(area_list)
    # Parse slots
    try:
        start_slot, end_slot = [int(x) for x in slot_text.split('-')]
        num_slots = abs(end_slot - start_slot) + 1
        row_bays = [f"{area_text}-{num:02d}" for num in range(start_slot, end_slot+1)]
    except:
        num_slots = 0
        row_bays = []
    # Actual Stack dengan Unit length
    df_match = df[(df['Area']==area_text) & (df['Row_Bay'].isin(row_bays))]
    if 'Unit length' in df_match.columns:
        try:
            actual_stack = int((df_match['Unit length']/20).sum())
        except:
            actual_stack = df_match.shape[0]
    else:
        actual_stack = df_match.shape[0]
    # Total Plan Capacity
    total_plan_capacity = num_areas * num_slots * height * multiplier
    plan_rows.append({
        "Area": area_text,
        "Slot": slot_text,
        "Height": height,
        "Num Areas": num_areas,
        "Num Slots": num_slots,
        "Total Plan Capacity": total_plan_capacity,
        "Actual Stack": actual_stack
    })
# Buat DataFrame
df_plan = pd.DataFrame(plan_rows)
    st.subheader("Summary Plan Capacity")
    st.dataframe(df_plan, use_container_width=True)
