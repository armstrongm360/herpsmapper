import json
import requests
import streamlit as st
import pydeck as pdk

# Your Cloudflare R2 Public Development URL (bucket public URL)
R2_PUBLIC = "https://pub-24f3dc7f88d741309e78eb1352612cfd.r2.dev"

# We don't know if your geojson files are in a subfolder or bucket root,
# so we try both.
CANDIDATE_PREFIXES = [
    f"{R2_PUBLIC}/polygon_export/",  # most likely
    f"{R2_PUBLIC}/",                 # bucket root
]

st.set_page_config(page_title="HerpsMapper", layout="wide")
st.title("HerpsMapper")
st.caption("Type a species (e.g., 'Gloydius brevicaudus') to load and render its polygon.")

species = st.text_input("Species name", placeholder="Genus species")

@st.cache_data(show_spinner=False, ttl=60 * 60)
def fetch_geojson(species_name: str) -> tuple[dict | None, str | None]:
    """
    Returns: (geojson_dict, url_used) or (None, None)
    """
    filename = species_name.strip().lower().replace(" ", "_") + ".geojson"

    headers = {
        "Accept": "application/json, text/plain, */*",
    }

    for prefix in CANDIDATE_PREFIXES:
        url = prefix + filename
        try:
            r = requests.get(url, headers=headers, timeout=30)
            if r.status_code == 200:
                return r.json(), url
        except requests.RequestException:
            continue

    return None, None

def bounds_center(geojson_obj: dict) -> tuple[float, float]:
    """
    Lightweight center estimate from GeoJSON coordinates (no shapely).
    Works for Polygon and MultiPolygon.
    """
    coords = []

    for feat in geojson_obj.get("features", []):
        geom = feat.get("geometry") or {}
        gtype = geom.get("type")
        gcoords = geom.get("coordinates") or []

        # Polygon: [ [ [lon,lat], ... ] , hole2...]
        # MultiPolygon: [ polygon1, polygon2, ... ]
        if gtype == "Polygon":
            rings = gcoords
            for ring in rings:
                coords.extend(ring)
        elif gtype == "MultiPolygon":
            for poly in gcoords:
                for ring in poly:
                    coords.extend(ring)

    if not coords:
        # fallback to China/Taiwan-ish center
        return 35.0, 105.0

    lons = [pt[0] for pt in coords if isinstance(pt, (list, tuple)) and len(pt) >= 2]
    lats = [pt[1] for pt in coords if isinstance(pt, (list, tuple)) and len(pt) >= 2]
    return (sum(lats) / len(lats), sum(lons) / len(lons))

if species and species.strip():
    with st.spinner("Loading polygon..."):
        geojson_obj, used_url = fetch_geojson(species)

    if geojson_obj is None:
        st.error("Polygon not found. Try a different species spelling.")
        st.write("This app expects files named like `genus_species.geojson` in your R2 bucket.")
        st.stop()

    st.success(f"Loaded polygon from: {used_url}")

    lat, lon = bounds_center(geojson_obj)

    layer = pdk.Layer(
        "GeoJsonLayer",
        data=geojson_obj,
        pickable=True,
        stroked=True,
        filled=True,
        extruded=False,
        line_width_min_pixels=1,
    )

    view_state = pdk.ViewState(latitude=lat, longitude=lon, zoom=4)

    st.pydeck_chart(pdk.Deck(layers=[layer], initial_view_state=view_state, tooltip={"text": "{shapefile}"}))

    with st.expander("Show raw GeoJSON"):
        st.json(geojson_obj)
else:
    st.info("Enter a species name above to render its polygon.")
