import streamlit as st
import requests
import json

# Streamlit frontend for getting GPS coordinates from the browser
def get_location_from_browser():
    # Frontend code to request GPS coordinates from the browser
    location_fetcher = """
    <script>
    function getLocation() {
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(showPosition, showError);
        } else { 
            alert("Geolocation is not supported by this browser.");
        }
    }

    function showPosition(position) {
        // Store coordinates in session storage and trigger a page reload
        sessionStorage.setItem('latitude', position.coords.latitude);
        sessionStorage.setItem('longitude', position.coords.longitude);
        // Trigger a Streamlit rerun by updating a hidden element
        window.parent.postMessage({
            type: 'streamlit:setComponentValue',
            value: {
                latitude: position.coords.latitude,
                longitude: position.coords.longitude
            }
        }, '*');
    }

    function showError(error) {
        let message = "Location access denied or unavailable.";
        switch(error.code) {
            case error.PERMISSION_DENIED:
                message = "User denied the request for Geolocation.";
                break;
            case error.POSITION_UNAVAILABLE:
                message = "Location information is unavailable.";
                break;
            case error.TIMEOUT:
                message = "The request to get user location timed out.";
                break;
            case error.UNKNOWN_ERROR:
                message = "An unknown error occurred.";
                break;
        }
        alert(message);
    }
    
    // Check if we already have coordinates
    if (sessionStorage.getItem('latitude') && sessionStorage.getItem('longitude')) {
        window.parent.postMessage({
            type: 'streamlit:setComponentValue',
            value: {
                latitude: parseFloat(sessionStorage.getItem('latitude')),
                longitude: parseFloat(sessionStorage.getItem('longitude'))
            }
        }, '*');
    } else {
        getLocation();
    }
    </script>
    """

    st.markdown(location_fetcher, unsafe_allow_html=True)
    
    # Use a different approach - manual input as fallback
    st.subheader("Location Input")
    col1, col2 = st.columns(2)
    
    with col1:
        latitude = st.number_input("Latitude", value=0.0, format="%.6f", key="lat_input")
    with col2:
        longitude = st.number_input("Longitude", value=0.0, format="%.6f", key="lon_input")
    
    if st.button("Use Current Location", key="get_location_btn"):
        st.markdown(location_fetcher, unsafe_allow_html=True)
        st.rerun()
    
    # Check if coordinates are provided
    if latitude != 0.0 and longitude != 0.0:
        st.success(f"Location: {latitude:.6f}, {longitude:.6f}")
        return latitude, longitude
    else:
        st.warning("Please enter coordinates or click 'Use Current Location'")
        return None, None

def main():
    st.title('GPS Location Finder')
    st.markdown("This app helps you get your current GPS coordinates.")
    
    # Initialize session state
    if 'location_data' not in st.session_state:
        st.session_state.location_data = None
    
    # Get location
    latitude, longitude = get_location_from_browser()
    
    if latitude is not None and longitude is not None:
        st.session_state.location_data = {'latitude': latitude, 'longitude': longitude}
        
        # Display the location information
        st.success("✅ Location found!")
        st.write(f"**Latitude:** {latitude:.6f}")
        st.write(f"**Longitude:** {longitude:.6f}")
        
        # Optional: Add a map or additional functionality
        if st.button("Get Address from Coordinates"):
            try:
                # You can add reverse geocoding here if needed
                st.info("Reverse geocoding functionality can be added here")
            except Exception as e:
                st.error(f"Error getting address: {e}")
    
    # Add some helpful information
    with st.expander("ℹ️ How to use this app"):
        st.markdown("""
        1. **Automatic Location**: Click "Use Current Location" to automatically detect your GPS coordinates
        2. **Manual Input**: Enter latitude and longitude manually if automatic detection doesn't work
        3. **Browser Permissions**: Make sure to allow location access when prompted by your browser
        4. **HTTPS Required**: For automatic location detection, the app needs to run over HTTPS
        """)

if __name__ == "__main__":
    main()
