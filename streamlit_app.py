import streamlit as st
import requests
import json

BASE_URL = "https://pub-24f3dc7f88d741309e78eb1352612cfd.r2.dev/polygon_export/"

st.title("HerpsMapper")

species = st.text_input("Enter species name:")

if species:

    species_file = species.lower().replace(" ", "_") + ".geojson"

    url = BASE_URL + species_file

    response = requests.get(url)

    if response.status_code == 200:

        geojson = response.json()

        st.success("Polygon loaded successfully")

        st.json(geojson)

    else:

        st.error("Species not found")