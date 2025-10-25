import streamlit as st
import streamlit.components.v1 as components

def get_location_from_browser():
    """Get GPS coordinates using browser geolocation API"""
    
    st.subheader("📍 Get Your Current Location")
    
    # Initialize session state
    if 'current_location' not in st.session_state:
        st.session_state.current_location = None
    
    # Button to trigger location detection
    if st.button("🌍 Use Current Location", type="primary"):
        # Inject JavaScript to get location
        components.html(
            """
            <script>
            function getLocation() {
                if (navigator.geolocation) {
                    navigator.geolocation.getCurrentPosition(
                        function(position) {
                            const lat = position.coords.latitude;
                            const lon = position.coords.longitude;
                            
                            // Send data to Streamlit
                            window.parent.postMessage({
                                type: 'streamlit:setComponentValue',
                                data: {latitude: lat, longitude: lon}
                            }, '*');
                            
                            // Also display on page
                            document.getElementById('result').innerHTML = 
                                '<p style="color: green; font-size: 16px;">✅ Location detected!<br>' +
                                'Latitude: ' + lat.toFixed(6) + '<br>' +
                                'Longitude: ' + lon.toFixed(6) + '<br>' +
                                '<strong>Copy these values to the input fields above!</strong></p>';
                        },
                        function(error) {
                            let errorMsg = '';
                            switch(error.code) {
                                case error.PERMISSION_DENIED:
                                    errorMsg = 'Permission denied. Please allow location access.';
                                    break;
                                case error.POSITION_UNAVAILABLE:
                                    errorMsg = 'Location unavailable.';
                                    break;
                                case error.TIMEOUT:
                                    errorMsg = 'Request timeout.';
                                    break;
                            }
                            document.getElementById('result').innerHTML = 
                                '<p style="color: red;">❌ ' + errorMsg + '</p>';
                        }
                    );
                } else {
                    document.getElementById('result').innerHTML = 
                        '<p style="color: red;">❌ Geolocation not supported by browser</p>';
                }
            }
            
            // Auto-trigger location request
            getLocation();
            </script>
            <div id="result" style="padding: 20px; font-family: sans-serif;">
                <p>🔄 Requesting location permission...</p>
            </div>
            """,
            height=150,
        )
        st.info("⚠️ Please allow location access when your browser prompts you, then copy the coordinates shown above into the input fields below.")
    
    st.markdown("---")
    
    # Manual input fields
    st.markdown("### 📝 Enter Coordinates")
    
    col1, col2 = st.columns(2)
    
    # Safe default values
    default_lat = 0.0
    default_lon = 0.0
    
    if st.session_state.current_location is not None:
        default_lat = st.session_state.current_location.get('latitude', 0.0)
        default_lon = st.session_state.current_location.get('longitude', 0.0)
    
    with col1:
        latitude = st.number_input(
            "Latitude", 
            value=default_lat, 
            format="%.6f", 
            key="lat_input",
            help="Enter latitude coordinate (e.g., 40.7128 for New York)"
        )
    with col2:
        longitude = st.number_input(
            "Longitude", 
            value=default_lon, 
            format="%.6f", 
            key="lon_input",
            help="Enter longitude coordinate (e.g., -74.0060 for New York)"
        )
    
    # Check if we have valid coordinates
    if latitude != 0.0 and longitude != 0.0:
        st.session_state.current_location = {'latitude': latitude, 'longitude': longitude}
        st.success(f"✅ Location set: {latitude:.6f}, {longitude:.6f}")
        return latitude, longitude
    else:
        st.warning("⚠️ Please enter coordinates or use the 'Use Current Location' button above")
        return None, None

def main():
    st.set_page_config(page_title="GPS Location Finder", page_icon="🌍")
    
    st.title('🌍 GPS Location Finder')
    st.markdown("This app helps you get your current GPS coordinates.")
    
    # Get location
    latitude, longitude = get_location_from_browser()
    
    if latitude is not None and longitude is not None:
        st.markdown("---")
        st.success("✅ Location Successfully Set!")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Latitude", f"{latitude:.6f}")
        with col2:
            st.metric("Longitude", f"{longitude:.6f}")
        
        # Show coordinates in different formats
        st.markdown("### 📋 Coordinate Formats")
        st.code(f"Decimal: {latitude:.6f}, {longitude:.6f}")
        st.code(f"Google Maps: https://www.google.com/maps?q={latitude},{longitude}")
        
        # Add clickable link
        st.markdown(f"[🗺️ View on Google Maps](https://www.google.com/maps?q={latitude},{longitude})")
    
    # Add some helpful information
    with st.expander("ℹ️ Troubleshooting & Alternative Methods"):
        st.markdown("""
        ### If the button doesn't work:
        
        **Method 1: Use get_location.html file**
        1. Open the `get_location.html` file in your browser
        2. Click "Get My Location" and allow access
        3. Copy the coordinates and paste them above
        
        **Method 2: Browser Console**
        1. Press F12 to open Developer Tools
        2. Go to Console tab
        3. Paste this code:
        ```javascript
        navigator.geolocation.getCurrentPosition(
            pos => console.log(`Lat: ${pos.coords.latitude}, Lon: ${pos.coords.longitude}`)
        );
        ```
        4. Allow location access
        5. Copy the coordinates from the console
        
        **Method 3: Google Maps**
        1. Go to Google Maps
        2. Right-click on your location
        3. Click on the coordinates to copy them
        4. Paste them in the input fields above
        
        **Common Issues:**
        - Browser blocks location in non-HTTPS sites (use alternative methods)
        - Location services disabled on device
        - Browser doesn't have location permission
        """)

if __name__ == "__main__":
    main()