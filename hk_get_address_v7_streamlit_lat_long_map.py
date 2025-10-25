import streamlit as st
import requests
import pandas as pd
import folium
from streamlit_folium import folium_static
from urllib.parse import quote

def lookup_address(address):
    """
    Performs a GET request to the address lookup service via a CORS proxy.
    
    Args:
        address (str): The address to look up.
    
    Returns:
        dict: The JSON response from the lookup service.
    """
    # URL encode the address
    encoded_address = quote(address)
    
    # Option 1: Try direct connection first
    url = f"https://www.als.ogcio.gov.hk/lookup?q={encoded_address}"
    headers = {
        "Accept": "application/json",
        "Accept-Language": "en,zh-Hant",
        "Accept-Encoding": "gzip",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.warning(f"Direct connection failed: {str(e)}")
        
        # Option 2: Try via CORS proxy (you'll need to set this up)
        # This is a placeholder - you need to deploy your own proxy
        st.error("""
        **Connection Failed**
        
        The Hong Kong government API cannot be accessed from Streamlit Cloud due to geographic restrictions.
        
        **Solutions:**
        1. **Deploy a proxy server** in Hong Kong and route requests through it
        2. **Use a VPN/proxy service** that allows API forwarding
        3. **Create a serverless function** (e.g., Vercel, Netlify) in Asia region
        4. **Run this app locally** where you can access the API directly
        
        **To run locally:**
        ```bash
        pip install streamlit requests pandas folium streamlit-folium
        streamlit run app.py
        ```
        """)
        return None

# Streamlit code
st.title('🏢 HK Address Lookup')

st.info("""
⚠️ **Note:** This app requires access to Hong Kong government APIs which may be restricted on Streamlit Cloud.
For best results, run this application locally or deploy it on infrastructure with Hong Kong network access.
""")

# User input for the address
address = st.text_input('Enter the address to look up', placeholder='e.g., Vivian Court, Central')

# Example addresses
with st.expander("📝 Example addresses to try"):
    st.write("""
    - Times Square, Causeway Bay
    - IFC Mall, Central
    - Victoria Harbour
    - Temple Street, Yau Ma Tei
    """)

# Button to perform the lookup
if st.button('🔍 Lookup', type="primary"):
    if not address.strip():
        st.warning("Please enter an address to look up.")
    else:
        with st.spinner('Looking up address...'):
            result = lookup_address(address)
        
        if result and 'SuggestedAddress' in result and len(result['SuggestedAddress']) > 0:
            st.success(f"Found {len(result['SuggestedAddress'])} address(es)")
            
            # Convert the result into a DataFrame
            df = pd.json_normalize(result['SuggestedAddress'])

            # Transpose the DataFrame
            df_transposed = df.transpose()

            # Display the transposed DataFrame
            st.subheader("Address Details")
            st.dataframe(df_transposed, use_container_width=True)

            # Create a map
            m = folium.Map(location=[22.3964, 114.1095], zoom_start=11)

            # Add markers to the map for each row
            markers_added = 0
            for i in range(df_transposed.shape[1]):
                try:
                    latitude = df_transposed.loc['Address.PremisesAddress.GeospatialInformation.Latitude', i]
                    longitude = df_transposed.loc['Address.PremisesAddress.GeospatialInformation.Longitude', i]
                    
                    # Check if coordinates are valid
                    if pd.notna(latitude) and pd.notna(longitude):
                        folium.Marker(
                            [latitude, longitude],
                            popup=f"Address {i+1}",
                            tooltip=f"Click for details"
                        ).add_to(m)
                        markers_added += 1
                except KeyError:
                    continue

            if markers_added > 0:
                st.subheader(f"📍 Map ({markers_added} location(s))")
                folium_static(m, width=700, height=500)
            else:
                st.warning("No geospatial coordinates available for the found addresses.")
                
        elif result:
            st.warning("No addresses found. Please try a different search term.")

# Add citation and instructions
st.markdown("---")
col1, col2 = st.columns(2)
with col1:
    st.markdown("**Data source:** Hong Kong Government Address Lookup Service")
with col2:
    st.markdown("**API:** `www.als.ogcio.gov.hk`")

# Add deployment instructions
with st.expander("🚀 Deployment Instructions"):
    st.markdown("""
    ### For Full Functionality:
    
    **Option 1: Run Locally**
    ```bash
    git clone <your-repo>
    cd <your-repo>
    pip install -r requirements.txt
    streamlit run app.py
    ```
    
    **Option 2: Deploy with Proxy**
    1. Create a serverless function in Hong Kong/Asia region
    2. Forward API requests through your proxy
    3. Update the `lookup_address()` function to use your proxy URL
    
    **Option 3: Use Alternative Hosting**
    - Deploy on a VPS in Hong Kong
    - Use cloud services with Hong Kong regions (AWS ap-east-1, GCP asia-east2)
    """)