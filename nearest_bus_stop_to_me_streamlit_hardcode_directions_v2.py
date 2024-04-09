import streamlit as st
import csv
from math import radians, cos, sin, asin, sqrt

def haversine_distance(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    r = 6371
    return c * r

def find_nearest_bus_stop(gps_file, lat, lon):
    nearest_stop = None
    nearest_stop_name_en = None
    nearest_stop_dir = None
    nearest_distance = float('inf')
    nearest_routes = []
    route_stops = {}
    nearest_lat = None
    nearest_lon = None

    with open(gps_file, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            stop_lat = float(row['lat'])
            stop_lon = float(row['long'])
            route = row['route']
            stop = (row['stop'], row['name_en'], row['dir'])
            if route not in route_stops:
                route_stops[route] = []
            route_stops[route].append(stop)
            distance = haversine_distance(lat, lon, stop_lat, stop_lon)
            if distance < nearest_distance:
                nearest_stop = row['stop']
                nearest_stop_name_en = row['name_en']
                nearest_stop_dir = row['dir']
                nearest_distance = distance
                nearest_routes = [route]
                nearest_lat = stop_lat
                nearest_lon = stop_lon
            elif distance == nearest_distance and route not in nearest_routes:
                nearest_routes.append(route)

    return nearest_stop, nearest_stop_name_en, nearest_stop_dir, nearest_distance, nearest_routes, route_stops, nearest_lat, nearest_lon

st.title('Find Nearest HK Bus Stop')

# Instructions on how to get GPS coordinates
st.sidebar.markdown("""
Instructions to get GPS with phone (Android):
1. Open the Maps app
2. Find current location (marked with blue dot on map)
3. Press and long hold on the blue dot  
4. enter the values based on pop up with gps coordinates on top

Instructions for iPhone
1. Open Maps app
2. Find current location (marked with blue dot on map)
3. Tap blue dot and see My Location at bottom
4. Swipe up from bottom bar to see GPS coordinates                                  
""")

# With this:
gps_input = st.text_input('Enter your GPS coordinates (e.g. 22.01657, 114.0126126)')

#lat = st.number_input('Enter your latitude')
#lon = st.number_input('Enter your longitude')

# Parse the input to extract latitude and longitude
try:
    lat, lon = map(float, gps_input.split(','))
except ValueError:
    st.error('Please enter valid GPS coordinates in the format "latitude, longitude"')
    st.stop()

gps_file = 'merged_bus_stop_data_complete.csv'  # Hardcoded GPS file path

if st.button('Find Nearest Bus Stop'):
    nearest_stop, nearest_stop_name_en, nearest_stop_dir, distance, routes, route_stops, nearest_lat, nearest_lon = find_nearest_bus_stop(gps_file, lat, lon)
    st.write(f"The nearest bus stop is '{nearest_stop}' ('{nearest_stop_name_en}'), direction '{nearest_stop_dir}', which is approximately {distance:.2f} km away.")
    st.markdown(f"GPS Coordinates for the nearest bus stop: {nearest_lat}, {nearest_lon}")
    st.markdown(f"[Click here to view on Google Maps](https://www.google.com/maps/search/?api=1&query={nearest_lat},{nearest_lon})")
    for route in routes:
        start_stop, start_stop_name_en, start_stop_dir = route_stops[route][0]
        end_stop, end_stop_name_en, end_stop_dir = route_stops[route][-1]
        st.write(f"Route: {route}, Start Stop: {start_stop} ('{start_stop_name_en}'), direction '{start_stop_dir}', End Stop: {end_stop} ('{end_stop_name_en}'), direction '{end_stop_dir}'")
