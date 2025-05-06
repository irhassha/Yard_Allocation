import streamlit as st
import pandas as pd

# Function to load data from an Excel file
@st.cache
def load_data():
    file_path = 'UnitListAll.xlsx'  # Ganti dengan path file kamu
    data = pd.read_excel(file_path, sheet_name='Unit List - All')
    return data

# Function to process and prepare the template
def process_data(data):
    areas = ['A01', 'A02', 'A03', 'A04', 'A05', 'A06', 'A07', 'A08']
    row_bays = [f"A01-{str(i).zfill(2)}" for i in range(1, 9)]

    final_template_unique = pd.DataFrame(columns=row_bays, index=areas)

    # Fill in the final template by iterating over the data
    for area in areas:
        for row in row_bays:
            # Extract all unique Carrier Out values for this Area and Row_Bay
            carrier_out_values = data[(data["Area"] == area) & (data["Row_Bay"] == row)]["Carrier Out"].unique()
            if len(carrier_out_values) > 0:
                final_template_unique.loc[area, row] = ', '.join(carrier_out_values)
            else:
                final_template_unique.loc[area, row] = ""

    return final_template_unique

# Main function to render the app
def main():
    st.title("Carrier Out Data Visualization")

    # Load the data
    data = load_data()

    # Process the data to generate the final table
    final_template = process_data(data)

    # Display the final template as a table
    st.write("Here is the table with unique Carrier Out values for each Row/Bay:")
    st.dataframe(final_template)

if __name__ == "__main__":
    main()
