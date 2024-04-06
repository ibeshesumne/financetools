import streamlit as st
import requests
import pandas as pd

def get_latest_json_data(url):
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        return None

# Add a title to the Streamlit app
st.title('Next Train')

# Load the data from the CSV file
df = pd.read_csv(r'next_train_data_dictionary.csv', delimiter=';')

# Extract unique line names
line_names = df['Line_name'].unique().tolist()

# Create dropdown boxes for line codes and stations in the sidebar

# Ask user to select a line name
selected_line_name = st.sidebar.selectbox("Select Line Name", ['Select...'] + line_names)

# If a line name has been selected
if selected_line_name != 'Select...':
    # Get the line code for the selected line name
    selected_line_code = df[df['Line_name'] == selected_line_name]['Line'].values[0]

    # Filter the DataFrame based on the selected line code
    filtered_df = df[df['Line'] == selected_line_code]

    # Extract the station names for the selected line code
    line_stations = filtered_df.sort_values('Station_name')[['Station_name', 'Station']].apply(lambda x: f"{x[0]} - {x[1]}", axis=1).unique().tolist()

    # Ask user to select a station for the selected line
    selected_station = st.sidebar.selectbox("Select Station for Selected Line", ['Select...'] + line_stations)

    # If a station has been selected
    if selected_station != 'Select...':
        # Get the station name and code for the selected station
        selected_station_name, selected_station_code = selected_station.split(' - ')

        # Use the function
        url = f'https://rt.data.gov.hk/v1/transport/mtr/getSchedule.php?line={selected_line_code}&sta={selected_station_code}'
        data = get_latest_json_data(url)
        print(f"Data received from API: {data}")

        if data and 'data' in data and f'{selected_line_code}-{selected_station_code}' in data['data']:
            station_data = data['data'][f'{selected_line_code}-{selected_station_code}']
            # Check if 'UP' and 'DOWN' data exist
            if 'UP' in station_data:
                up_data = station_data['UP']
                df_up = pd.DataFrame(up_data)
                st.header('UP Data')
                st.dataframe(df_up)
            if 'DOWN' in station_data:
                down_data = station_data['DOWN']
                df_down = pd.DataFrame(down_data)
                st.header('DOWN Data')
                st.dataframe(df_down)
        elif 'error' in data and 'errorMsg' in data['error']:
            st.error(f"Error from API: {data['error']['errorMsg']}")
        else:
            st.error('Invalid data received from API')

# Add a source to the Streamlit app
st.markdown("Source data: MTR Corporation Limited")
