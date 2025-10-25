import streamlit as st
import requests
import pandas as pd
import folium
from streamlit_folium import folium_static
from urllib.parse import quote

def lookup_address(address):
    """
    Performs a GET request to the address lookup service.
    
    Args:
        address (str): The address to look up.
    
    Returns:
        dict: The JSON response from the lookup service.
    """
    # URL encode the address
    encoded_address = quote(address)
    
    # Try multiple methods to access the API
    proxies_to_try = [
        # Method 1: Direct connection
        {
            "url": f"https://www.als.ogcio.gov.hk/lookup?q={encoded_address}",
            "headers": {
                "Accept": "application/json",
                "Accept-Language": "en,zh-Hant",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
        },
        # Method 2: Using allorigins.win proxy
        {
            "url": f"https://api.allorigins.win/raw?url={quote(f'https://www.als.ogcio.gov.hk/lookup?q={encoded_address}')}",
            "headers": {
                "Accept": "application/json"
            }
        },
        # Method 3: Using corsproxy.io
        {
            "url": f"https://corsproxy.io/?{quote(f'https://www.als.ogcio.gov.hk/lookup?q={encoded_address}')}",
            "headers": {
                "Accept": "application/json"
            }
        }
    ]
    
    last_error = None
    
    for i, proxy_config in enumerate(proxies_to_try):
        try:
            response = requests.get(
                proxy_config["url"], 
                headers=proxy_config["headers"], 
                timeout=15
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Validate we got actual address data
            if isinstance(data, dict) and 'SuggestedAddress' in data:
                if i > 0:
                    st.info(f"✅ Connected successfully using proxy method {i+1}")
                return data
            
        except Exception as e:
            last_error = str(e)
            continue
    
    # All methods failed
    st.error(f"""
    **Unable to Connect to Hong Kong Address API**
    
    All connection methods failed. Last error: {last_error[:200]}
    
    **This is likely because:**
    - Streamlit Cloud servers cannot access Hong Kong government APIs
    - Geographic/network restrictions are in place
    
    **Recommended Solutions:**
    
    1. **Run Locally (Easiest):**
    ```bash
    pip install streamlit requests pandas folium streamlit-folium
    streamlit run app.py
    ```
    
    2. **Deploy on Hong Kong Infrastructure:**
    - Use AWS Hong Kong region (ap-east-1)
    - Use Google Cloud Hong Kong region (asia-east2)
    - Deploy on a Hong Kong VPS
    
    3. **Create Your Own Proxy:**
    - Deploy a serverless function in Asia
    - Route requests through your own proxy server
    """)
    
    return None

# Streamlit code
st.title('🏢 HK Address Lookup')

st.info("""
⚠️ **Important:** The Hong Kong government API may not be accessible from Streamlit Cloud.
If you see connection errors, please run this app locally or deploy on Hong Kong infrastructure.
""")

# User input for the address
address = st.text_input(
    'Enter the address to look up', 
    placeholder='e.g., Times Square, Causeway Bay',
    help='Enter any Hong Kong address in English or Chinese'
)

# Example addresses
with st.expander("📝 Example addresses to try"):
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Times Square, Causeway Bay"):
            st.session_state.address = "Times Square, Causeway Bay"
        if st.button("IFC Mall, Central"):
            st.session_state.address = "IFC Mall, Central"
    with col2:
        if st.button("Victoria Harbour"):
            st.session_state.address = "Victoria Harbour"
        if st.button("Temple Street"):
            st.session_state.address = "Temple Street"

# Update address from session state
if 'address' in st.session_state:
    address = st.session_state.address

# Button to perform the lookup
if st.button('🔍 Lookup Address', type="primary"):
    if not address.strip():
        st.warning("⚠️ Please enter an address to look up.")
    else:
        with st.spinner('🔄 Searching for address...'):
            result = lookup_address(address)
        
        if result and 'SuggestedAddress' in result and len(result['SuggestedAddress']) > 0:
            st.success(f"✅ Found {len(result['SuggestedAddress'])} address(es)")
            
            # Convert the result into a DataFrame
            df = pd.json_normalize(result['SuggestedAddress'])

            # Transpose the DataFrame
            df_transposed = df.transpose()

            # Display the transposed DataFrame
            st.subheader("📋 Address Details")
            st.dataframe(df_transposed, use_container_width=True)
            
            # Download option
            csv = df_transposed.to_csv()
            st.download_button(
                label="📥 Download as CSV",
                data=csv,
                file_name=f"hk_address_{address[:30]}.csv",
                mime="text/csv"
            )

            # Create a map
            st.subheader("🗺️ Location Map")
            m = folium.Map(location=[22.3964, 114.1095], zoom_start=11)

            # Add markers to the map for each row
            markers_added = 0
            locations = []
            
            for i in range(df_transposed.shape[1]):
                try:
                    latitude = df_transposed.loc['Address.PremisesAddress.GeospatialInformation.Latitude', i]
                    longitude = df_transposed.loc['Address.PremisesAddress.GeospatialInformation.Longitude', i]
                    
                    # Check if coordinates are valid
                    if pd.notna(latitude) and pd.notna(longitude):
                        # Try to get address text for popup
                        try:
                            addr_text = df_transposed.loc['Address.PremisesAddress.EngPremisesAddress.EngDistrict.DcDistrict', i]
                        except:
                            addr_text = f"Location {i+1}"
                        
                        folium.Marker(
                            [latitude, longitude],
                            popup=folium.Popup(addr_text, max_width=300),
                            tooltip=f"Address {i+1}",
                            icon=folium.Icon(color='red', icon='info-sign')
                        ).add_to(m)
                        
                        locations.append([latitude, longitude])
                        markers_added += 1
                except KeyError:
                    continue

            if markers_added > 0:
                # Fit map to markers
                if len(locations) > 1:
                    m.fit_bounds(locations)
                elif len(locations) == 1:
                    m.location = locations[0]
                    m.zoom_start = 16
                    
                folium_static(m, width=700, height=500)
                st.caption(f"📍 Showing {markers_added} location(s) on map")
            else:
                st.warning("⚠️ No geospatial coordinates available for the found addresses.")
                
        elif result:
            st.warning("⚠️ No addresses found. Please try a different search term.")

# Add citation and instructions
st.markdown("---")
col1, col2 = st.columns(2)
with col1:
    st.markdown("**Data source:** Hong Kong Government")
    st.markdown("**API:** Address Lookup Service")
with col2:
    st.markdown("**Website:** [www.als.ogcio.gov.hk](https://www.als.ogcio.gov.hk)")

# Add deployment instructions
with st.expander("💡 Troubleshooting & Local Setup"):
    st.markdown("""
    ### If the app doesn't work on Streamlit Cloud:
    
    **Quick Local Setup:**
    ```bash
    # Clone and install
    pip install streamlit requests pandas folium streamlit-folium
    
    # Run the app
    streamlit run app.py
    ```
    
    **Why it might not work on Streamlit Cloud:**
    - Geographic restrictions on Hong Kong government APIs
    - DNS resolution blocked from Streamlit's infrastructure
    - Network security policies
    
    **Alternative Deployment Options:**
    - AWS EC2 in Hong Kong (ap-east-1)
    - Google Cloud in Hong Kong (asia-east2)
    - DigitalOcean Singapore datacenter
    - Local development environment
    """)