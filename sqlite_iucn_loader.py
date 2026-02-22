# sqlite_iucn_loader.py
import os
import sqlite3
import json
from flask import Blueprint, request, jsonify
from shapely import wkt
from shapely.geometry import mapping

sqlite_iucn_bp = Blueprint("sqlite_iucn", __name__)

# Path to your SQLite database (adjust if necessary)
DB_PATH = "species_index.db"

@sqlite_iucn_bp.route("/get_iucn_polygon_sqlite")
def get_iucn_polygon_sqlite():
    species_input = request.args.get("species", "").strip()
    species = species_input.lower()
    print(f"DEBUG: Received species query: '{species_input}' (normalized to '{species}')")
    if not species:
        return jsonify({"error": "No species provided"}), 400

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Debug: Retrieve and print all species in the database (raw values)
        cursor.execute("SELECT species FROM species_index")
        all_species = [row[0] for row in cursor.fetchall()]
        print("DEBUG: All species in database (raw):", all_species)

        # Execute a case-insensitive query using LOWER()
        query = "SELECT shapefile, wkt FROM species_index WHERE LOWER(species) = ?"
        print(f"DEBUG: Executing query: {query} with parameter: {species}")
        cursor.execute(query, (species,))
        rows = cursor.fetchall()
        print(f"DEBUG: Query returned {len(rows)} rows")
        conn.close()
    except Exception as e:
        print("DEBUG: Database error:", e)
        return jsonify({"error": f"Database error: {e}"}), 500

    if not rows:
        return jsonify({
            "error": f"IUCN polygon data not found for '{species_input}'. "
                     "This species appears in the reptile database but is not indexed in our SQLite database. "
                     "Please try the search box."
        }), 404

    features = []
    for shapefile, wkt_str in rows:
        try:
            geom = wkt.loads(wkt_str)
            geom_geojson = mapping(geom)
        except Exception as e:
            print(f"DEBUG: Error converting WKT for species '{species_input}' in file '{shapefile}': {e}")
            continue

        feature = {
            "type": "Feature",
            "geometry": geom_geojson,
            "properties": {"shapefile": shapefile}
        }
        features.append(feature)

    result = {"type": "FeatureCollection", "features": features}
    print("DEBUG: Returning feature collection with", len(features), "features")
    return jsonify(result), 200, {"Content-Type": "application/json"}
