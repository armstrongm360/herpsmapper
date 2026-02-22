import streamlit as st
import pandas as pd
import requests
import folium
from streamlit_folium import st_folium

# Your public R2 base (must end with a slash)
R2_BASE = "https://pub-24f3dc7f88d741309e78eb1352612cfd.r2.dev/polygon_export/"

st.set_page_config(page_title="HerpsMapper", layout="wide")
st.title("HerpsMapper")


@st.cache_data(show_spinner=False)
def load_species_list() -> list[str]:
    """
    Tries to load species list from all_reptiles_world.csv.
    Falls back to an empty list if file isn't in the repo.
    """
    try:
        df = pd.read_csv("all_reptiles_world.csv")
        if "species" not in df.columns:
            return []
        species = (
            df["species"]
            .dropna()
            .astype(str)
            .str.strip()
            .str.replace(r"\s+", " ", regex=True)
            .unique()
            .tolist()
        )
        cleaned = []
        for s in species:
            parts = s.split()
            if parts:
                parts[0] = parts[0].capitalize()
            cleaned.append(" ".join(parts))
        return sorted(set(cleaned))
    except Exception:
        return []


def species_to_filename(species_name: str) -> str:
    return species_name.strip().lower().replace(" ", "_") + ".geojson"


def fetch_polygon_geojson(species_name: str):
    url = R2_BASE + species_to_filename(species_name)
    r = requests.get(url, timeout=30)
    if r.status_code == 200:
        return r.json(), url
    return None, url


def fetch_inat_points(species_name: str, limit: int = 500):
    """
    Lightweight iNaturalist fetch: grabs up to 'limit' points.
    (Flask version streams + paginates; keep this simple for Streamlit.)
    """
    api = "https://api.inaturalist.org/v1/observations"
    params = {
        "taxon_name": species_name,
        "per_page": min(limit, 200),
        "page": 1,
        "verifiable": "true",
    }
    r = requests.get(api, params=params, timeout=30)
    r.raise_for_status()
    data = r.json()
    pts = []
    for obs in data.get("results", []):
        geo = obs.get("geojson")
        if geo and geo.get("type") == "Point":
            lon, lat = geo.get("coordinates", [None, None])
            if lat is not None and lon is not None:
                pts.append((lat, lon))
    return pts, data.get("total_results", 0)


species_list = load_species_list()

left, right = st.columns([1, 2])

with left:
    st.subheader("Controls")

    if species_list:
        species = st.selectbox(
            "Choose a species (type to search):",
            options=species_list,
            index=0,
        )
    else:
        species = st.text_input("Species name (e.g., Gloydius brevicaudus):")

    load_poly = st.button("Load polygon (R2)", type="primary")
    load_inat = st.button("Load iNaturalist points (quick)")
    st.caption("Polygons are loaded from Cloudflare R2.")

with right:
    st.subheader("Map")

    # China-focused start (matches your original intent better than global)
    m = folium.Map(location=[35, 105], zoom_start=4, tiles="OpenTopoMap")

    if species and load_poly:
        geojson, url = fetch_polygon_geojson(species)
        if geojson:
            folium.GeoJson(
                geojson,
                name="IUCN polygon",
                style_function=lambda _: {
                    "color": "red",
                    "weight": 2,
                    "fillOpacity": 0.4,
                },
            ).add_to(m)
            folium.LayerControl().add_to(m)
            st.success(f"Polygon loaded from: {url}")
        else:
            st.error(f"Polygon not found at: {url}")

    if species and load_inat:
        try:
            pts, total = fetch_inat_points(species, limit=500)
            for lat, lon in pts:
                folium.CircleMarker(
                    location=[lat, lon],
                    radius=3,
                    color="darkred",
                    fill=True,
                    fill_opacity=0.9,
                    weight=1,
                ).add_to(m)
            st.info(f"Loaded {len(pts)} points (of ~{total} total iNat observations).")
        except Exception as e:
            st.error(f"iNaturalist fetch failed: {e}")

    st_folium(m, height=650, use_container_width=True)
