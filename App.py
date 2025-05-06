import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import matplotlib.colors as mcolors

# Data (update dengan data Anda)
data = {
    'Area': ['A01'] * 10 + ['B01'] * 10,
    'Move': ['Export'] * 20,
    'Carrier Out': ['ORNEL', 'ORNEL', 'ORNEL', 'ORNEL', 'ORNEL', 
                    'MERAN', 'MERAN', 'MERAN', 'MERAN', 'MERAN', 
                    'MERAN', 'MERAN', 'MERAN', 'JOSEP', 'JOSEP',
                    'ORNEL', 'ORNEL', 'ORNEL', 'ORNEL', 'ORNEL'],
    'Row_Bay': ['A01-03', 'A01-03', 'A01-03', 'A01-03', 'A01-07', 
                'A01-07', 'A01-03', 'A01-03', 'A01-07', 'A01-07',
                'B01-03', 'B01-03', 'B01-03', 'B01-03', 'B01-07',
                'B01-07', 'B01-03', 'B01-07', 'B01-03', 'B01-07']
}

# Convert data to DataFrame
df = pd.DataFrame(data)

# Group by Area, Row_Bay, and Carrier Out and count occurrences
df_grouped = df.groupby(['Area', 'Row_Bay', 'Carrier Out']).size().unstack(fill_value=0)

# Define colors for each unique Carrier Out
unique_carriers = df['Carrier Out'].unique()
colors = list(mcolors.TABLEAU_COLORS.values())

# Create a mapping of Carrier Out to colors
carrier_color_map = {carrier: colors[i % len(colors)] for i, carrier in enumerate(unique_carriers)}

# Create the stacked bar chart with Plotly
fig = go.Figure()

# Loop through each Area and create separate bar charts
for area in df_grouped.index.get_level_values('Area').unique():
    df_area = df_grouped.loc[area]
    
    # Add bars for each Carrier Out in that area
    for carrier in df_area.columns:
        fig.add_trace(go.Bar(
            x=df_area.index,
            y=df_area[carrier],
            name=f'{area} - {carrier}',
            marker_color=carrier_color_map[carrier],  # Original color for each carrier
            hoverinfo='x+y+name',  # Show name, x, and y values on hover
            opacity=0.7,  # Set opacity for all categories
        ))

# Update layout to remove grid lines and set axis labels
fig.update_layout(
    title='Stacked Visualization of Carrier Out in Each Row_Bay',
    xaxis_title='Row_Bay',
    yaxis_title='Count of Carrier Out',
    barmode='stack',
    xaxis=dict(tickmode='array', tickvals=df_grouped.index.get_level_values('Row_Bay').unique()),
    showlegend=True,
    legend_title='Carrier Out',
    template='plotly_dark',  # Update template for dark theme like the example
    height=700
)

# Display the figure using Streamlit
st.plotly_chart(fig)
