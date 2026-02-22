# iucn_loader.py
import os
import geopandas as gpd
from flask import Blueprint, request, jsonify

iucn_bp = Blueprint("iucn", __name__)

# Define the folder where the shapefiles reside.
IUCN_FOLDER = os.path.join("IUCN_files", "reptilia_polygon")


@iucn_bp.route("/get_iucn_polygon")
def get_iucn_polygon():
    species = request.args.get("species")
    if not species:
        return jsonify({"error": "No species provided"}), 400

    species_clean = species.strip().lower()
    # List all shapefiles in the IUCN folder.
    shp_files = [
        os.path.join(IUCN_FOLDER, f)
        for f in os.listdir(IUCN_FOLDER)
        if f.lower().endswith(".shp")
    ]
    if not shp_files:
        return jsonify({"error": "No shapefiles found in the IUCN folder"}), 500

    matching_features = None
    for shp in shp_files:
        try:
            gdf = gpd.read_file(shp)
            # Use an exact, case-insensitive match on the "sci_name" field.
            filtered = gdf[gdf["sci_name"].str.strip().str.lower() == species_clean]
            if not filtered.empty:
                matching_features = filtered
                break  # Stop if we found a match.
        except Exception as e:
            print(f"Error reading {shp}: {e}")
            continue

    if matching_features is None or matching_features.empty:
        return (
            jsonify({"error": f"No IUCN polygon data found for species: {species}"}),
            404,
        )

    # Return the filtered features as GeoJSON.
    geojson_str = matching_features.to_json()
    return geojson_str, 200, {"Content-Type": "application/json"}
