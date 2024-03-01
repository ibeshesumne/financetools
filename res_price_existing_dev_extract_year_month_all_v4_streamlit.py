# use government api to download and extract existing development property prices
# plot the nominal price line chart
# download from government website an inflation measure
# generate a real property price series from nominal property price series
# plot three charts that show: nominal price, inflation, and real price
# plot a chart that shows the percentage change in real price

import streamlit as st
import requests
import pandas as pd
import re
import matplotlib.pyplot as plt

# Function to fetch and prepare data
def fetch_data():
    url = 'https://api.data.gov.hk/v2/filter?q=%7B%22resource%22%3A%22http%3A%2F%2Fwww.rvd.gov.hk%2Fdoc%2Fen%2Fstatistics%2Fhis_data_5.xls%22%2C%22section%22%3A1%2C%22format%22%3A%22json%22%7D'
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        extracted_data = [{re.sub(r'[^\x00-\x7F]+',' ', key): item.get(key, None) for key in item} for item in data]
        df = pd.DataFrame(extracted_data)

        # Remove asterisks from '  Month' values
        df['  Month'] = df['  Month'].str.replace('*', '')

        # Combine '  Year' and '  Month' into a single 'Datetime' column
        df['Datetime'] = pd.to_datetime(df['  Year'] + '-' + df['  Month'], errors='coerce')

        # Drop the original '  Year' and '  Month' columns
        df = df.drop(['  Year', '  Month'], axis=1)

        # Rename 'Datetime' to 'Period'
        df = df.rename(columns={'Datetime': 'Period'})

        # Move 'Period' column to the first position
        df = df.set_index('Period').reset_index()

        df.columns = df.columns.str.strip()

        df = df.dropna()

        return df

    else:
        st.error('Error fetching data:', response.status_code)
        return None

# Fetch data
df = fetch_data()

# List of columns to plot
columns_to_plot = ['Urban [A, B & C -   Urban][]', 'N.T. [A, B & C -   N.T.][]', 'Urban [  Overall -   Urban][]', 'N.T. [  Overall -   N.T.][]', 'All [  Overall -   All][]']

# User selection
selected_column = st.selectbox('Select a series to display', columns_to_plot)

# Plot selected column
st.subheader('Time Series Plot')
plt.plot(df['Period'], df[selected_column], label=selected_column)
plt.title('Time Series Plot')
plt.grid(True, which='both', color='0.9', linewidth=0.4)
plt.xlabel('Period')
plt.ylabel('Value')
plt.legend()
st.pyplot(plt)

# Calculate year-on-year change in percentage
df[selected_column + '_yoy'] = df[selected_column].pct_change(12) * 100

# Clear the current figure
plt.clf()

# Plot year-on-year change in percentage
st.subheader('Year on Year Change in the Nominal Price for Each Series (%)')
plt.plot(df['Period'], df[selected_column + '_yoy'], label=selected_column + '_yoy')
plt.title('Year on Year Change in the Nominal Price for Each Series (%)')
plt.grid(True, which='both', color='0.9', linewidth=0.4)
plt.xlabel('Period')
plt.ylabel('Change (%)')
plt.legend()
st.pyplot(plt)