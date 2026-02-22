# weather.py
from datetime import datetime
import pandas as pd
from meteostat import Monthly

def fetch_station_weather(station_id, start_date, end_date):
    """
    Fetch monthly weather data for a given Meteostat station.
    station_id: Meteostat station identifier.
    start_date, end_date: Strings in "YYYY-MM-DD" format.
    
    Returns:
        A Pandas DataFrame with monthly data (columns include 'tavg' and 'prcp').
    """
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    try:
        data = Monthly(station_id, start, end)
        df = data.fetch()
        if 'tavg' not in df.columns and 'tmin' in df.columns and 'tmax' in df.columns:
            df['tavg'] = (df['tmin'] + df['tmax']) / 2
        return df[['tavg', 'prcp']]
    except Exception as e:
        print(f"Error fetching monthly weather data for station {station_id}: {e}")
        return None

def combine_station_weather(station_ids, station_map, start_date, end_date):
    """
    Fetch monthly weather data for each station in station_ids and combine them.
    station_map is a dict mapping station id to its coordinates (unused here but kept for compatibility).
    
    Returns:
        A DataFrame with the mean values for each month (index is the month number).
    """
    station_dfs = []
    for sid in station_ids:
        df = fetch_station_weather(sid, start_date, end_date)
        if df is not None and not df.empty:
            df.index = pd.to_datetime(df.index)
            df.index = df.index.month
            station_dfs.append(df)
    if not station_dfs:
        return None
    combined_df = pd.concat(station_dfs).groupby(level=0).mean()
    return combined_df
