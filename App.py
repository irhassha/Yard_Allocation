import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import matplotlib.colors as mcolors

# Data (you can replace this with your actual data source)
data = {
    'Area': ['A01'] * 20,
    'Move': ['Export'] * 20,
    'Carrier Out': ['ORNEL', 'ORNEL', 'ORNEL', 'ORNEL', 'ORNEL', 
                    'MERAN', 'MERAN', 'MERAN', 'MERAN', 'MERAN', 
                    'MERAN', 'MERAN', 'MERAN', 'JOSEP', 'JOSEP',
                    'ORNEL', 'ORNEL', 'ORNEL', 'ORNEL', 'ORNEL'],
    'Row_Bay': ['A01-03', 'A01-03', 'A01-03', 'A01-03', 'A01-03', 
                'A01-03', 'A01-03', 'A01-03', 'A01-03', 'A01-03', 
                'A01-03', 'A01-03', 'A01-03', 'A01-07', 'A01-07', 
                'A01-07', 'A01-07', 'A01-07', 'A01-07', 'A01-07']
}

# Convert data to DataFrame
df = pd.DataFrame(data)

# Group by Row_Bay and Carrier Out and count occurrences
df_grouped = df.groupby(['Row_Bay', 'Carrier Out']).size().unstack(fill_value=0)

# Define colors for each unique Carrier Out
unique_carriers = df['Carrier Out'].unique()
colors = list(mcolors.TABLEAU_COLORS.values())

# Create a mapping of Carrier Out to colors
carrier_color_map = {carrier: colors[i % len(colors)] for i, carrier in enumerate(unique_carriers)}

# Neutral gray color
gray_color = '#d3d3d3'

# Create the stacked bar chart with Plotly
fig = go.Figure()

# Add bars for each Carrier Out
for carrier in df_grouped.columns:
    fig.add_trace(go.Bar(
        x=df_grouped.index,
        y=df_grouped[carrier],
        name=carrier,
        marker_color=carrier_color_map[carrier] if carrier in st.session_state.get('selected_carriers', []) else gray_color,
        hoverinfo='x+y+name',  # Show name, x, and y values on hover
        opacity=1 if carrier in st.session_state.get('selected_carriers', []) else 0.3,  # Reduce opacity for unselected
    ))

# Update layout to remove grid lines and set axis labels
fig.update_layout(
    title='Stacked Visualization of Carrier Out in Each Row_Bay',
    xaxis_title='Row_Bay',
    yaxis_title='Count of Carrier Out',
    barmode='stack',
    xaxis=dict(tickmode='array', tickvals=df_grouped.index),
    showlegend=True,
    legend_title='Carrier Out',
    template='plotly_white'
)

# Handle legend selection/deselection to highlight carriers
if 'selected_carriers' not in st.session_state:
    st.session_state.selected_carriers = unique_carriers.tolist()  # Select all by default

# Display the figure using Streamlit
st.plotly_chart(fig)
