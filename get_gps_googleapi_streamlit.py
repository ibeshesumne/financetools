import streamlit as st
from streamlit_cropper import st_cropper
import requests

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
        document.getElementById("latitude").value = position.coords.latitude;
        document.getElementById("longitude").value = position.coords.longitude;
        document.getElementById("locationForm").submit();
    }

    function showError(error) {
        switch(error.code) {
            case error.PERMISSION_DENIED:
                alert("User denied the request for Geolocation.");
                break;
            case error.POSITION_UNAVAILABLE:
                alert("Location information is unavailable.");
                break;
            case error.TIMEOUT:
                alert("The request to get user location timed out.");
                break;
            case error.UNKNOWN_ERROR:
                alert("An unknown error occurred.");
                break;
        }
    }
    getLocation();
    </script>
    """

    # HTML form to submit the coordinates to the server
    form = """
    <form id="locationForm" action="" method="post">
        <input type="hidden" id="latitude" name="latitude">
        <input type="hidden" id="longitude" name="longitude">
    </form>
    """
    st.markdown(location_fetcher, unsafe_allow_html=True)
    st.markdown(form, unsafe_allow_html=True)

    # Checking if the coordinates are submitted
    latitude = st.session_state.get('latitude', None)
    longitude = st.session_state.get('longitude', None)
    if latitude and longitude:
        st.write(f"Latitude: {latitude}, Longitude: {longitude}")
    else:
        st.write("Waiting for location...")

def main():
    st.title('GPS Location Finder')

    if st.button('Get Location'):
        get_location_from_browser()

if __name__ == "__main__":
    main()
