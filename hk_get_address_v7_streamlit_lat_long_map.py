import streamlit as st
import requests
import pandas as pd
import folium
from streamlit_folium import folium_static

def lookup_address(address):
    """
    Performs a GET request to the address lookup service and returns the response.
    
    Args:
        address (str): The address to look up, URL-encoded.
    
    Returns:
        dict: The JSON response from the lookup service.
    """
    url = f"https://www.als.ogcio.gov.hk/lookup?q={address}"
    headers = {
        "Accept": "application/json",
        "Accept-Language": "en,zh-Hant",
        "Accept-Encoding": "gzip"
    }
    
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

# Streamlit code
st.title('HK Address Lookup')

# User input for the address
address = st.text_input('Enter the address to look up')

# Button to perform the lookup
if st.button('Lookup'):
    result = lookup_address(address)

    # Convert the result into a DataFrame
    df = pd.json_normalize(result['SuggestedAddress'])

    # Transpose the DataFrame
    df_transposed = df.transpose()

    # Display the transposed DataFrame
    st.write(df_transposed)

    # Create a map
    m = folium.Map(location=[22.3964, 114.1095], zoom_start=11)  # Initial location is set to Hong Kong

    # Add markers to the map for each row
    for i in range(df_transposed.shape[1]):
        latitude = df_transposed.loc['Address.PremisesAddress.GeospatialInformation.Latitude', i]
        longitude = df_transposed.loc['Address.PremisesAddress.GeospatialInformation.Longitude', i]
        folium.Marker([latitude, longitude]).add_to(m)

    # Display the map
    folium_static(m)