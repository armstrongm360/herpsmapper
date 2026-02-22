import requests
from flask import Blueprint, request, jsonify

sqlite_iucn_bp = Blueprint("sqlite_iucn", __name__)

BASE_URL = "https://pub-24f3dc7f88d741309e78eb1352612cfd.r2.dev/polygon_export/"


@sqlite_iucn_bp.route("/get_iucn_polygon_sqlite")
def get_iucn_polygon_sqlite():

    species_input = request.args.get("species", "").strip()

    if not species_input:
        return jsonify({"error": "No species provided"}), 400

    species_file = species_input.lower().replace(" ", "_") + ".geojson"

    url = BASE_URL + species_file

    response = requests.get(url)

    if response.status_code != 200:

        return jsonify({"error": f"Polygon not found for {species_input}"}), 404

    return jsonify(response.json())
