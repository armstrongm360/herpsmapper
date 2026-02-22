import json
import requests
import streamlit as st
import folium
from streamlit_folium import st_folium

import data_loader

# --- CONFIG ---
R2_BASE_URL = "https://pub-24f3dc7f88d741309e78eb1352612cfd.r2.dev/polygon_export/"
CHINA_CENTER = [33.0, 105.0]  # roughly centered on China
CHINA_ZOOM = 4

st.set_page_config(page_title="HerpsMapper", layout="wide")
st.title("HerpsMapper — China/Taiwan Climate & Distribution Explorer")

# --- LOAD DATA (cached) ---
@st.cache_data(show_spinner=False)
def load_orders_and_species():
    # Reads ./species_files/*.txt (must be in repo)
    return data_loader.load_herp_orders()

@st.cache_data(show_spinner=False)
def load_china_weather_stations():
    # Uses Meteostat bounds (54,73) to (18,136) from your original code
    return data_loader.load_weather_stations()

herp_orders = load_orders_and_species()
stations = load_china_weather_stations()

# --- UI: dropdowns like the Flask app ---
left, right = st.columns([1, 2])

with left:
    st.subheader("1) Choose a species (dropdown)")
    orders = sorted(list(herp_orders.keys()))
    selected_order = st.selectbox("Herp Order (China/Taiwan)", options=orders)

    species_list = herp_orders.get(selected_order, [])
    selected_species = st.selectbox("Species", options=species_list)

    st.divider()
    st.subheader("2) Polygons (IUCN)")
    show_iucn = st.button("Show IUCN Distribution (Polygon)", use_container_width=True)

    st.subheader("3) iNaturalist")
    show_inat = st.button("Show iNaturalist Distribution", use_container_width=True)

    st.caption("Map starts focused on China/Taiwan (same intent as the Flask version).")

# --- SESSION STATE ---
if "iucn_geojson" not in st.session_state:
    st.session_state.iucn_geojson = None
if "inat_points" not in st.session_state:
    st.session_state.inat_points = []

# --- ACTIONS ---
def fetch_iucn_geojson(species_name: str):
    # Your R2 naming convention: "genus_species.geojson"
    species_file = species_name.strip().lower().replace(" ", "_") + ".geojson"
    url = R2_BASE_URL + species_file
    r = requests.get(url, timeout=30)
    if r.status_code != 200:
        return None, url
    return r.json(), url

def fetch_inat_points(species_name: str, max_points: int = 2000):
    # Simple iNat fetch (keeps it Streamlit-friendly)
    inat_url = "https://api.inaturalist.org/v1/observations"
    params = {
        "taxon_name": species_name,
        "per_page": 200,
        "order": "desc",
        "verifiable": "true",
        "page": 1,
    }

    points = []
    while True:
        r = requests.get(inat_url, params=params, timeout=30)
        if r.status_code != 200:
            break
        data = r.json()
        results = data.get("results", [])
        if not results:
            break

        for obs in results:
            geo = obs.get("geojson")
            if geo and geo.get("type") == "Point":
                coords = geo.get("coordinates")  # [lng, lat]
                if coords and len(coords) == 2:
                    points.append([coords[1], coords[0]])  # [lat, lng]
                    if len(points) >= max_points:
                        return points

        if len(results) < params["per_page"]:
            break
        params["page"] += 1

    return points

with right:
    st.subheader("Map (China/Taiwan focus)")

    # Build base map
    m = folium.Map(location=CHINA_CENTER, zoom_start=CHINA_ZOOM, tiles="OpenStreetMap")

    # Add weather stations as markers
    for s in stations:
        lat, lng = s["coords"]
        folium.CircleMarker(
            location=[lat, lng],
            radius=3,
            popup=f'{s["id"]} — {s["name"]}',
            tooltip=f'{s["id"]} — {s["name"]}',
            fill=True,
        ).add_to(m)

    # Add IUCN polygon if loaded
    if st.session_state.iucn_geojson:
        folium.GeoJson(
            st.session_state.iucn_geojson,
            name="IUCN Polygon",
        ).add_to(m)

    # Add iNat points if loaded
    if st.session_state.inat_points:
        for lat, lng in st.session_state.inat_points[:1500]:
            folium.CircleMarker(
                location=[lat, lng],
                radius=1,
                fill=True,
            ).add_to(m)

    # Render map
    st_folium(m, height=650, width=None)

# Trigger buttons AFTER map rendering logic is ready
if show_iucn:
    with st.spinner("Loading IUCN polygon from R2..."):
        geojson, url = fetch_iucn_geojson(selected_species)
        if geojson is None:
            st.error(f"Polygon not found for: {selected_species}")
            st.info(f"Tried: {url}")
        else:
            st.session_state.iucn_geojson = geojson
            st.success("Loaded polygon (IUCN). Scroll up to see it on the map.")

if show_inat:
    with st.spinner("Loading iNaturalist observations..."):
        pts = fetch_inat_points(selected_species)
        if not pts:
            st.error("No iNaturalist points returned (or API failed).")
        else:
            st.session_state.inat_points = pts
            st.success(f"Loaded {len(pts)} iNaturalist points. Scroll up to see them.")
