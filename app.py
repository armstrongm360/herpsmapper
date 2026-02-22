import sys, os

# When bundled by PyInstaller, sys.frozen is True and _MEIPASS is the temp folder
if getattr(sys, 'frozen', False):
    base_dir = sys._MEIPASS
else:
    base_dir = os.path.dirname(os.path.abspath(__file__))

# Change CWD so that all relative opens() work off base_dir
os.chdir(base_dir)

from flask import Flask, render_template, request, jsonify, Response
import json, traceback
import data_loader
import weather
import inat
from iucn_loader import iucn_bp  # Make sure this file exists
import webbrowser
import threading
from sqlite_iucn_loader import sqlite_iucn_bp
import csv
import pandas as pd

app = Flask(__name__)
app.register_blueprint(iucn_bp)  # Register the IUCN blueprint AFTER app is created
app.register_blueprint(sqlite_iucn_bp)

# Load herp orders from species_files.
herp_orders = data_loader.load_herp_orders()

@app.route("/")
def index():
    # For the initial page load, load stations covering China/Taiwan.
    station_list = data_loader.load_weather_stations()
    orders = list(herp_orders.keys())
    return render_template(
        "index.html",
        orders=orders,
        herp_orders_json=json.dumps(herp_orders),
        station_list_json=json.dumps(station_list)
    )

@app.route("/stations")
def stations():
    try:
        north = float(request.args.get("north"))
        west = float(request.args.get("west"))
        south = float(request.args.get("south"))
        east = float(request.args.get("east"))
        station_list = data_loader.get_stations_by_bounds(north, west, south, east)
        return jsonify(station_list)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route("/generate_graph", methods=["POST"])
def generate_graph():
    try:
        data = request.get_json()
        species = data.get("species")
        selected_station_ids = data.get("selectedStations", [])
        if not selected_station_ids:
            return jsonify({"error": "Please select at least one weather station to generate the graph."}), 400

        stations = data_loader.load_weather_stations()
        station_map = {s['id']: s['coords'] for s in stations}

        start_date = "2015-01-01"
        end_date = "2025-04-01"

        combined_df = weather.combine_station_weather(selected_station_ids, station_map, start_date, end_date)
        if combined_df is None:
            return jsonify({"error": "Failed to retrieve weather data."}), 500

        all_results, total_obs = inat.fetch_all_inat_data(species, force=False)
        obs_df = inat.aggregate_inat_observations(all_results)

        final_df = combined_df.join(obs_df, how="outer").fillna(0)
        final_df = final_df.sort_index()
        grouped = final_df.groupby(final_df.index).mean()

        month_labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        temperature_list = []
        precipitation_list = []
        observations_list = []
        for m in range(1, 13):
            if m in grouped.index:
                temperature_list.append(float(grouped.loc[m, "tavg"]))
                precipitation_list.append(float(grouped.loc[m, "prcp"]))
                observations_list.append(int(grouped.loc[m, "observations"]))
            else:
                temperature_list.append(None)
                precipitation_list.append(None)
                observations_list.append(0)

        response_data = {
            "months": month_labels,
            "temperature": temperature_list,
            "precipitation": precipitation_list,
            "observations": observations_list,
            "total_obs": total_obs
        }
        return jsonify(response_data)
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route("/fetch_inat_data")
def fetch_inat_data():
    species = request.args.get("species")
    if not species:
        return "Species not provided", 400

    def generate():
        for msg in inat.stream_inat_data(species, force=False):
            yield f"data: {msg}\n\n"
    return Response(generate(), mimetype="text/event-stream")

@app.route("/get_station_climate")
def get_station_climate():
    station_id = request.args.get("station_id")
    if not station_id:
        return jsonify({"error": "No station_id provided"}), 400

    start_date = "2015-01-01"
    end_date = "2025-04-01"
    df = weather.fetch_station_weather(station_id, start_date, end_date)
    if df is None or df.empty:
        return jsonify({"error": "No climate data available for station"}), 404

    # Reset index so that the date becomes a column.
    df = df.reset_index()

    # Meteostat typically names the date column "time". If not, check for "index".
    if "time" in df.columns:
        try:
            df["month"] = pd.to_datetime(df["time"]).dt.month
        except Exception as e:
            print(f"Error processing 'time' column: {e}")
    elif "index" in df.columns:
        try:
            df["month"] = pd.to_datetime(df["index"]).dt.month
        except Exception as e:
            print(f"Error processing 'index' column: {e}")

    # If we still don't have a "month" column, return an error.
    if "month" not in df.columns:
        return jsonify({"error": "Climate data format error: 'month' column missing"}), 500

    data = df[["month", "tavg", "prcp"]].to_dict(orient="records")
    return jsonify(data)

@app.route("/report")
def report_page():
    # Render the new report page template.
    return render_template("report.html")

@app.route("/run_report")
def run_report():
    # Import the report generator module and stream progress updates.
    import reptile_report_generator as rrg
    def generate():
        for msg in rrg.generate_report_stream():
            yield f"data: {msg}\n\n"
    return Response(generate(), mimetype="text/event-stream")

@app.route("/get_report")
def get_report():
    try:
        with open("reptile_discrepancy_report.txt", "r", encoding="utf-8") as f:
            report = f.read()
        return jsonify({"report": report})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/species_suggestions")
def species_suggestions():
    query = request.args.get("query", "").strip().lower()
    suggestions = []
    if len(query) < 4:
        return jsonify({"suggestions": suggestions})
    # Load species from CSV (IUCN file)
    iucn_species = set()
    try:
        with open("all_reptiles_world.csv", "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                sp = row.get("species", "").strip().lower()
                if sp:
                    iucn_species.add(sp)
    except Exception as e:
        print("Error reading all_reptiles_world.csv:", e)
    # Load species from text files (RD file)
    rd_species = set()
    species_folder = "species_files"
    if os.path.isdir(species_folder):
        for filename in os.listdir(species_folder):
            if filename.lower().endswith(".txt"):
                try:
                    with open(os.path.join(species_folder, filename), "r", encoding="utf-8") as f:
                        for line in f:
                            sp = line.strip().lower()
                            if sp:
                                rd_species.add(sp)
                except Exception as e:
                    print("Error reading", filename, e)
    all_species = iucn_species.union(rd_species)
    for sp in all_species:
        if query in sp:
            sources = []
            if sp in rd_species:
                sources.append("RD file")
            if sp in iucn_species:
                sources.append("IUCN file")
            if len(sources) == 2:
                source_str = "Both files"
            elif sources:
                source_str = sources[0]
            else:
                source_str = ""
            # Format species name: capitalize the genus (first word)
            parts = sp.split()
            if parts:
                parts[0] = parts[0].capitalize()
            formatted_name = " ".join(parts)
            suggestions.append({"name": formatted_name, "sources": source_str})
    suggestions = sorted(suggestions, key=lambda x: x["name"])
    return jsonify({"suggestions": suggestions})

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
