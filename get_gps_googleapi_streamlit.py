import streamlit as st
import requests
import json

def get_location_from_browser():
    """Get GPS coordinates using a simple and reliable approach"""
    
    st.subheader("📍 Get Your Current Location")
    
    # Initialize session state
    if 'current_location' not in st.session_state:
        st.session_state.current_location = None
    
    # Manual input fields
    col1, col2 = st.columns(2)
    
    with col1:
        latitude = st.number_input(
            "Latitude", 
            value=st.session_state.current_location['latitude'] if st.session_state.current_location else 0.0, 
            format="%.6f", 
            key="lat_input",
            help="Enter latitude coordinate (e.g., 40.7128 for New York)"
        )
    with col2:
        longitude = st.number_input(
            "Longitude", 
            value=st.session_state.current_location['longitude'] if st.session_state.current_location else 0.0, 
            format="%.6f", 
            key="lon_input",
            help="Enter longitude coordinate (e.g., -74.0060 for New York)"
        )
    
    # Location detection section
    st.markdown("---")
    st.markdown("### 🌍 Automatic Location Detection")
    
    # Instructions for manual location detection
    st.info("""
    **To get your current location automatically:**
    1. Open your browser's developer tools (F12)
    2. Go to the Console tab
    3. Copy and paste this code:
    ```javascript
    navigator.geolocation.getCurrentPosition(function(position) {
        console.log('Latitude: ' + position.coords.latitude);
        console.log('Longitude: ' + position.coords.longitude);
        alert('Latitude: ' + position.coords.latitude + ', Longitude: ' + position.coords.longitude);
    });
    ```
    4. Press Enter and allow location access when prompted
    5. Copy the coordinates and paste them into the fields above
    """)
    
    # Alternative: Use a simple HTML page approach
    st.markdown("### 🔧 Alternative Method")
    st.markdown("""
    **Or use this HTML page to get your coordinates:**
    """)
    
    html_code = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Get My Location</title>
    </head>
    <body>
        <h2>Get My Current Location</h2>
        <button onclick="getLocation()">Get My Location</button>
        <p id="location"></p>
        
        <script>
        function getLocation() {
            if (navigator.geolocation) {
                navigator.geolocation.getCurrentPosition(showPosition, showError);
            } else {
                document.getElementById("location").innerHTML = "Geolocation is not supported by this browser.";
            }
        }
        
        function showPosition(position) {
            document.getElementById("location").innerHTML = 
                "Latitude: " + position.coords.latitude + "<br>" +
                "Longitude: " + position.coords.longitude;
        }
        
        function showError(error) {
            let message = "Error: ";
            switch(error.code) {
                case error.PERMISSION_DENIED:
                    message += "User denied the request for Geolocation.";
                    break;
                case error.POSITION_UNAVAILABLE:
                    message += "Location information is unavailable.";
                    break;
                case error.TIMEOUT:
                    message += "The request to get user location timed out.";
                    break;
                default:
                    message += "An unknown error occurred.";
                    break;
            }
            document.getElementById("location").innerHTML = message;
        }
        </script>
    </body>
    </html>
    """
    
    st.code(html_code, language='html')
    st.markdown("Save this as an HTML file and open it in your browser to get your coordinates.")
    
    # Check if we have valid coordinates
    if latitude != 0.0 and longitude != 0.0:
        st.session_state.current_location = {'latitude': latitude, 'longitude': longitude}
        st.success(f"✅ Location set: {latitude:.6f}, {longitude:.6f}")
        return latitude, longitude
    else:
        st.warning("⚠️ Please enter coordinates manually using one of the methods above")
        return None, None

def main():
    st.title('🌍 GPS Location Finder')
    st.markdown("This app helps you get your current GPS coordinates using multiple methods.")
    
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
        
        # Optional: Add a map or additional functionality
        st.markdown("### 🗺️ Additional Options")
        if st.button("Get Address from Coordinates"):
            try:
                # You can add reverse geocoding here if needed
                st.info("Reverse geocoding functionality can be added here")
            except Exception as e:
                st.error(f"Error getting address: {e}")
        
        # Show coordinates in different formats
        st.markdown("### 📋 Coordinate Formats")
        st.code(f"Decimal: {latitude:.6f}, {longitude:.6f}")
        st.code(f"Google Maps: https://www.google.com/maps?q={latitude},{longitude}")
    
    # Add some helpful information
    with st.expander("ℹ️ How to use this app"):
        st.markdown("""
        ### Method 1: Browser Console (Recommended)
        1. Open browser developer tools (F12)
        2. Go to Console tab
        3. Copy and paste the JavaScript code shown above
        4. Allow location access when prompted
        5. Copy the coordinates and enter them manually
        
        ### Method 2: HTML File
        1. Copy the HTML code shown above
        2. Save it as a `.html` file
        3. Open the file in your browser
        4. Click "Get My Location" button
        5. Copy the coordinates and enter them manually
        
        ### Method 3: Manual Entry
        - Look up your coordinates on Google Maps
        - Right-click on your location and select coordinates
        - Enter them in the fields above
        
        **Note**: Automatic location detection in Streamlit apps requires HTTPS and can be unreliable. The methods above are more reliable.
        """)

if __name__ == "__main__":
    main()
