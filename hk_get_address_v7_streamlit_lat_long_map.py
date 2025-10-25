import streamlit as st
import requests
import pandas as pd
import folium
from streamlit_folium import folium_static
from urllib.parse import quote
import json

# Sample mock data for demonstration when API is unavailable
MOCK_DATA = {
    "Times Square": {
        "SuggestedAddress": [
            {
                "Address": {
                    "PremisesAddress": {
                        "EngPremisesAddress": {
                            "BuildingName": "TIMES SQUARE",
                            "EngStreet": {"StreetName": "MATHESON STREET", "BuildingNoFrom": "1"},
                            "EngDistrict": {"DcDistrict": "Wan Chai District", "Region": "HK"}
                        },
                        "ChiPremisesAddress": {
                            "BuildingName": "時代廣場",
                            "Region": "香港"
                        },
                        "GeoAddress": "4128183467T19940101",
                        "GeospatialInformation": {
                            "Latitude": 22.2783,
                            "Longitude": 114.1824,
                            "Northing": 834678,
                            "Easting": 841281
                        }
                    }
                },
                "ValidationInformation": {"Score": 95}
            }
        ]
    },
    "IFC": {
        "SuggestedAddress": [
            {
                "Address": {
                    "PremisesAddress": {
                        "EngPremisesAddress": {
                            "BuildingName": "INTERNATIONAL FINANCE CENTRE",
                            "EngStreet": {"StreetName": "FINANCE STREET", "BuildingNoFrom": "8"},
                            "EngDistrict": {"DcDistrict": "Central & Western District", "Region": "HK"}
                        },
                        "ChiPremisesAddress": {
                            "BuildingName": "國際金融中心",
                            "Region": "香港"
                        },
                        "GeoAddress": "3393083421T20030515",
                        "GeospatialInformation": {
                            "Latitude": 22.2852,
                            "Longitude": 114.1584,
                            "Northing": 834210,
                            "Easting": 833930
                        }
                    }
                },
                "ValidationInformation": {"Score": 98}
            }
        ]
    }
}

def lookup_address_with_params(address, max_results=10, tolerance=35, basic_mode=False):
    """
    Performs address lookup with additional API parameters.
    
    Args:
        address: Address to search
        max_results: Maximum number of results (1-200)
        tolerance: Score tolerance (0-80)
        basic_mode: Enable basic search mode (no fuzzy matching)
    """
    encoded_address = quote(address)
    
    # Build URL with optional parameters
    params = f"q={encoded_address}&n={max_results}&t={tolerance}"
    if basic_mode:
        params += "&b=1"
    
    url = f"https://www.als.ogcio.gov.hk/lookup?{params}"
    
    headers = {
        "Accept": "application/json",
        "Accept-Language": "en,zh-Hant",
        "Accept-Encoding": "gzip",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        return response.json(), False
    except:
        # Try CORS proxies
        proxies = [
            f"https://api.allorigins.win/raw?url={quote(url)}",
            f"https://corsproxy.io/?{quote(url)}"
        ]
        
        for proxy_url in proxies:
            try:
                response = requests.get(proxy_url, timeout=15)
                response.raise_for_status()
                return response.json(), False
            except:
                continue
        
        # Return mock data if all connections fail
        for key in MOCK_DATA:
            if key.lower() in address.lower():
                return MOCK_DATA[key], True
        
        return None, False

# Streamlit UI
st.title('🏢 HK Address Lookup Service')

# Sidebar with settings
with st.sidebar:
    st.header("⚙️ Search Settings")
    max_results = st.slider("Max Results", 1, 50, 10, help="Maximum number of addresses to return (API limit: 200)")
    tolerance = st.slider("Score Tolerance", 0, 80, 35, help="Lower = stricter matching")
    basic_mode = st.checkbox("Basic Search Mode", help="Disable fuzzy/phonetic matching")
    
    st.markdown("---")
    st.markdown("**API Parameters:**")
    st.code(f"n={max_results}\nt={tolerance}\nb={1 if basic_mode else 0}")

# Main content
tab1, tab2, tab3 = st.tabs(["🔍 Search", "📖 API Info", "ℹ️ About"])

with tab1:
    st.info("⚠️ **Note:** API may not be accessible from Streamlit Cloud. Mock data will be used as fallback.")
    
    # Search input
    address = st.text_input(
        'Enter address to search',
        placeholder='e.g., Times Square, IFC, Victoria Harbour',
        help='Enter building name, street name, or estate name'
    )
    
    # Quick examples
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🏢 Times Square"):
            address = "Times Square"
    with col2:
        if st.button("🏦 IFC Mall"):
            address = "IFC"
    with col3:
        if st.button("🏛️ Central"):
            address = "Central"
    
    # Search button
    if st.button('🔍 Search Address', type="primary", use_container_width=True):
        if not address.strip():
            st.warning("⚠️ Please enter an address")
        else:
            with st.spinner('🔄 Searching...'):
                result, is_mock = lookup_address_with_params(address, max_results, tolerance, basic_mode)
            
            if is_mock:
                st.warning("⚠️ Using demo data - API unavailable from Streamlit Cloud")
            
            if result and 'SuggestedAddress' in result and len(result['SuggestedAddress']) > 0:
                st.success(f"✅ Found {len(result['SuggestedAddress'])} address(es)")
                
                # Convert to DataFrame
                df = pd.json_normalize(result['SuggestedAddress'])
                
                # Display summary table
                st.subheader("📋 Search Results")
                
                summary_data = []
                for i, row in df.iterrows():
                    try:
                        summary_data.append({
                            "Building": row.get('Address.PremisesAddress.EngPremisesAddress.BuildingName', 'N/A'),
                            "District": row.get('Address.PremisesAddress.EngPremisesAddress.EngDistrict.DcDistrict', 'N/A'),
                            "Score": row.get('ValidationInformation.Score', 'N/A'),
                            "Latitude": row.get('Address.PremisesAddress.GeospatialInformation.Latitude', 'N/A'),
                            "Longitude": row.get('Address.PremisesAddress.GeospatialInformation.Longitude', 'N/A')
                        })
                    except:
                        continue
                
                if summary_data:
                    summary_df = pd.DataFrame(summary_data)
                    st.dataframe(summary_df, use_container_width=True)
                
                # Full details expander
                with st.expander("📄 View Full JSON Response"):
                    st.json(result)
                
                # Download button
                csv = df.to_csv(index=False)
                st.download_button(
                    "📥 Download CSV",
                    csv,
                    f"hk_address_{address[:20]}.csv",
                    "text/csv"
                )
                
                # Map
                st.subheader("🗺️ Location Map")
                m = folium.Map(location=[22.3193, 114.1694], zoom_start=12)
                
                markers_added = 0
                locations = []
                
                for i, row in df.iterrows():
                    try:
                        lat = row['Address.PremisesAddress.GeospatialInformation.Latitude']
                        lon = row['Address.PremisesAddress.GeospatialInformation.Longitude']
                        
                        if pd.notna(lat) and pd.notna(lon):
                            building = row.get('Address.PremisesAddress.EngPremisesAddress.BuildingName', f'Location {i+1}')
                            district = row.get('Address.PremisesAddress.EngPremisesAddress.EngDistrict.DcDistrict', 'Unknown')
                            score = row.get('ValidationInformation.Score', 'N/A')
                            
                            popup_text = f"<b>{building}</b><br>{district}<br>Score: {score}"
                            
                            folium.Marker(
                                [lat, lon],
                                popup=folium.Popup(popup_text, max_width=300),
                                tooltip=building,
                                icon=folium.Icon(color='red', icon='home')
                            ).add_to(m)
                            
                            locations.append([lat, lon])
                            markers_added += 1
                    except:
                        continue
                
                if markers_added > 0:
                    if len(locations) > 1:
                        m.fit_bounds(locations)
                    elif len(locations) == 1:
                        m.location = locations[0]
                        m.zoom_start = 16
                    
                    folium_static(m, width=700, height=500)
                    st.caption(f"📍 {markers_added} location(s) displayed")
                else:
                    st.warning("No geospatial data available")
            else:
                st.error("❌ No results found. Try a different search term.")

with tab2:
    st.header("📖 API Documentation")
    
    st.markdown("""
    ### API Endpoint
    ```
    GET https://www.als.ogcio.gov.hk/lookup
    ```
    
    ### Parameters
    | Parameter | Type | Range | Default | Description |
    |-----------|------|-------|---------|-------------|
    | `q` | string | - | required | Address to search (URL-encoded) |
    | `n` | integer | 1-200 | 200 | Max number of results |
    | `t` | integer | 0-80 | 35 | Score tolerance |
    | `b` | integer | 0-1 | 0 | Basic mode (1=no fuzzy matching) |
    | `3d` | integer | 0-1 | 0 | Show floor/unit info |
    
    ### Response Format
    Returns JSON with structured address data including:
    - English and Chinese addresses
    - Geospatial coordinates (Latitude/Longitude)
    - District and region information
    - GeoAddress identifier
    - Matching score
    
    ### Example Request
    ```
    https://www.als.ogcio.gov.hk/lookup?q=Times%20Square&n=10&t=35
    ```
    """)

with tab3:
    st.header("ℹ️ About This App")
    
    st.markdown("""
    ### HK Address Lookup Service
    
    This application provides a user-friendly interface to the Hong Kong Government's 
    Address Lookup Service API.
    
    **Features:**
    - 🔍 Search addresses by building name, street, or estate
    - 🗺️ Interactive map visualization
    - 📊 Detailed address information
    - 📥 Export results to CSV
    - ⚙️ Customizable search parameters
    
    **Data Source:** Hong Kong SAR Government  
    **API:** Address Lookup Service (ALS)  
    **Documentation:** [Digital Policy Office](https://www.digitalpolicy.gov.hk)
    
    ### Running Locally
    ```bash
    pip install streamlit requests pandas folium streamlit-folium
    streamlit run app.py
    ```
    
    ### Known Limitations
    - API may not be accessible from Streamlit Cloud
    - Geographic restrictions may apply
    - Rate limiting on API requests
    
    For production use, deploy on Hong Kong-based infrastructure or run locally.
    """)

st.markdown("---")
st.caption("Data source: Hong Kong Government Address Lookup Service | © HKSAR Government")