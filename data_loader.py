# data_loader.py
import os
import pandas as pd
from meteostat import Stations

def load_species_from_file(filepath):
    """Load species list from a single text file."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]
    except Exception as e:
        print(f"Error loading {filepath}: {e}")
        return []

def load_herp_orders(species_folder="species_files"):
    """
    Load species from all .txt files in the species_files folder.
    Uses the file name (without extension) as the order key.
    """
    herp_orders = {}
    if not os.path.isdir(species_folder):
        print(f"Species folder '{species_folder}' does not exist.")
        return herp_orders

    for filename in os.listdir(species_folder):
        if filename.endswith(".txt"):
            filepath = os.path.join(species_folder, filename)
            order_name = os.path.splitext(filename)[0].title()
            herp_orders[order_name] = load_species_from_file(filepath)
    return herp_orders

def load_weather_stations():
    """
    Query weather stations from Meteostat using a bounding box
    that covers Mainland China and Taiwan:
      - Top Left: (54, 73)  -> 54°N, 73°E
      - Bottom Right: (18, 136) -> 18°N, 136°E

    Returns a list of dictionaries with keys:
      - id: Meteostat station identifier
      - name: Station name
      - coords: [latitude, longitude]
      - country: ISO country code
      - elevation: station elevation (if available)
      - monthly_start: first day on record for monthly data (as string)
      - monthly_end: last day on record for monthly data (as string)
    """
    try:
        stations_df = Stations().bounds((54, 73), (18, 136)).fetch().reset_index()
        print(f"DEBUG: Number of stations found for initial view: {len(stations_df)}")

        station_list = []
        for _, row in stations_df.iterrows():
            ms = row['monthly_start']
            me = row['monthly_end']
            monthly_start = ms.strftime("%Y-%m-%d") if pd.notnull(ms) else None
            monthly_end = me.strftime("%Y-%m-%d") if pd.notnull(me) else None

            station_list.append({
                'id': row['id'],
                'name': row['name'],
                'coords': [row['latitude'], row['longitude']],
                'country': row['country'],
                'elevation': row.get('elevation', None),
                'monthly_start': monthly_start,
                'monthly_end': monthly_end
            })
        return station_list
    except Exception as e:
        print(f"Error fetching weather stations: {e}")
        return []

def get_stations_by_bounds(north, west, south, east):
    """
    Query weather stations from Meteostat that fall within the specified bounding box.
    Args: north, west, south, east -> bounding coordinates.

    Returns a list of station dictionaries (same structure as load_weather_stations()).
    """
    import pandas as pd
    try:
        stations_df = Stations().bounds((north, west), (south, east)).fetch().reset_index()
        print(f"DEBUG: Number of stations found in bounds: {len(stations_df)}")

        station_list = []
        for _, row in stations_df.iterrows():
            ms = row['monthly_start']
            me = row['monthly_end']
            monthly_start = ms.strftime("%Y-%m-%d") if pd.notnull(ms) else None
            monthly_end = me.strftime("%Y-%m-%d") if pd.notnull(me) else None

            station_list.append({
                'id': row['id'],
                'name': row['name'],
                'coords': [row['latitude'], row['longitude']],
                'country': row['country'],
                'elevation': row.get('elevation', None),
                'monthly_start': monthly_start,
                'monthly_end': monthly_end
            })
        return station_list
    except Exception as e:
        print(f"Error fetching stations by bounds: {e}")
        return []
