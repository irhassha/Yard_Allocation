import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import matplotlib.colors as mcolors

st.set_page_config(layout="wide", page_title="Carrier Out per Area")

# —————— Data contoh baru ——————
data = {
    'Area': [
        'A01','A01','A01','A01',
        'A02','A02','A02',
        'B01','B01','B01','B01','B01',
        'B02','B02','B02'
    ],
    'Move': ['Export'] * 15,
    'Carrier Out': [
        'ORNEL','MERAN','JOSEP','ORNEL',
        'ORNEL','ORNEL','MERAN',
        'MERAN','SIDEC','JOSEP','MERAN','SIDEC',
        'MERAN','JOSEP','JOSEP'
    ],
    'Row_Bay': [
        'A01-03','A01-03','A01-03','A01-07',
        'A02-03','A02-07','A02-07',
        'B01-03','B01-03','B01-03','B01-07','B01-07',
        'B02-03','B02-03','B02-07'
    ]
}

# —————— Load DataFrame ——————
df = pd.DataFrame(data)

# —————— Setup warna ——————
unique_carriers = df['Carrier Out'].unique().tolist()
palette = list(mcolors.TABLEAU_COLORS.values())
carrier_color_map = {c: palette[i % len(palette)] for i, c in enumerate(unique_carriers)}
gray = '#555555'

# —————— Sidebar highlight ——————
st.sidebar.markdown("### Highlight Carrier Out")
selected = st.sidebar.multiselect(
    "Pilih carrier:",
    options=unique_carriers,
    default=unique_carriers
)

# —————— Plot per Area ——————
for area in sorted(df['Area'].unique()):
    df_area = df[df['Area'] == area]
    df_grp = df_area.groupby(['Row_Bay','Carrier Out']).size().unstack(fill_value=0)

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
        xaxis=dict(title='', showgrid=False),
        yaxis=dict(title='', showgrid=True, showticklabels=False),
        legend_title='Carrier Out',
        margin=dict(t=20, b=20, l=20, r=20),
        height=350
    )

    fig.add_annotation(
        text=area,
        xref='paper', yref='paper',
        x=0.98, y=0.02,
        showarrow=False,
        font=dict(size=14, color='lightgray'),
        xanchor='right', yanchor='bottom'
    )

    st.plotly_chart(fig, use_container_width=True)
