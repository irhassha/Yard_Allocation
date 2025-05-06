import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import matplotlib.colors as mcolors

st.set_page_config(layout="wide", page_title="Carrier Out per Area")

# —————— Data (ganti dg data asli atau baca dari sumber kamu) ——————
data = {
    'Area': ['A01'] * 10 + ['B01'] * 10,
    'Move': ['Export'] * 20,
    'Carrier Out': [
        'ORNEL','ORNEL','ORNEL','ORNEL','ORNEL',
        'MERAN','MERAN','MERAN','MERAN','MERAN',
        'MERAN','MERAN','MERAN','JOSEP','JOSEP',
        'ORNEL','ORNEL','ORNEL','ORNEL','ORNEL'
    ],
    'Row_Bay': [
        'A01-03','A01-03','A01-03','A01-07','A01-07',
        'A01-03','A01-03','A01-07','A01-07','A01-03',
        'B01-03','B01-03','B01-03','B01-03','B01-07',
        'B01-07','B01-03','B01-07','B01-03','B01-07'
    ]
}
df = pd.DataFrame(data)

# —————— Setup warna untuk Carrier Out ——————
unique_carriers = df['Carrier Out'].unique().tolist()
palette = list(mcolors.TABLEAU_COLORS.values())
carrier_color_map = {c: palette[i % len(palette)] for i, c in enumerate(unique_carriers)}
gray = '#555555'

# —————— Widget untuk memilih Carrier Out yang di-highlight ——————
st.sidebar.markdown("### Highlight Carrier Out")
selected = st.sidebar.multiselect(
    "Pilih carrier yang di-highlight",
    options=unique_carriers,
    default=unique_carriers
)

# —————— Loop per Area dan gambar chart ——————
for area in df['Area'].unique():
    st.subheader(f"Area {area}")
    df_a = df[df['Area'] == area]
    df_grp = df_a.groupby(['Row_Bay','Carrier Out']).size().unstack(fill_value=0)
    
    fig = go.Figure()
    for carrier in df_grp.columns:
        is_sel = carrier in selected
        fig.add_trace(go.Bar(
            x=df_grp.index,
            y=df_grp[carrier],
            name=carrier,
            marker_color=carrier_color_map[carrier] if is_sel else gray,
            opacity=1.0 if is_sel else 0.3
        ))
    
    fig.update_layout(
        barmode='stack',
        template='plotly_dark',
        xaxis_title='Row_Bay',
        yaxis_title='Count of Carrier Out',
        legend_title='Carrier Out',
        margin=dict(t=40, b=40, l=20, r=20),
        height=400
    )
    st.plotly_chart(fig, use_container_width=True)
