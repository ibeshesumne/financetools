import streamlit as st
import requests
import pandas as pd
import folium
from streamlit_folium import folium_static
from urllib.parse import quote

def lookup_address(address):
    """
    Performs a GET request to the address lookup service and returns the response.
    
    Args:
        address (str): The address to look up.
    
    Returns:
        dict: The JSON response from the lookup service.
    """
    # URL encode the address
    encoded_address = quote(address)
    url = f"https://www.als.ogcio.gov.hk/lookup?q={encoded_address}"
    headers = {
        "Accept": "application/json",
        "Accept-Language": "en,zh-Hant",
        "Accept-Encoding": "gzip"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        st.error("Request timed out. Please try again.")
        return None
    except requests.exceptions.ConnectionError:
        st.error("Connection error. Please check your internet connection or try again later.")
        return None
    except requests.exceptions.HTTPError as e:
        st.error(f"HTTP error occurred: {e}")
        return None
    except Exception as e:
        st.error(f"An unexpected error occurred: {str(e)}")
        return None

# Streamlit code
st.title('HK Address Lookup')

# User input for the address
address = st.text_input('Enter the address to look up')

# Button to perform the lookup
if st.button('Lookup'):
    if not address.strip():
        st.warning("Please enter an address to look up.")
    else:
        with st.spinner('Looking up address...'):
            result = lookup_address(address)
        
        if result and 'SuggestedAddress' in result and len(result['SuggestedAddress']) > 0:
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
                try:
                    latitude = df_transposed.loc['Address.PremisesAddress.GeospatialInformation.Latitude', i]
                    longitude = df_transposed.loc['Address.PremisesAddress.GeospatialInformation.Longitude', i]
                    
                    # Check if coordinates are valid
                    if pd.notna(latitude) and pd.notna(longitude):
                        folium.Marker([latitude, longitude]).add_to(m)
                except KeyError:
                    # Skip if geospatial information is not available
                    continue

            # Display the map
            folium_static(m)
        elif result:
            st.warning("No addresses found. Please try a different search term.")

# Add citation
st.markdown("Data source: Hong Kong government.")