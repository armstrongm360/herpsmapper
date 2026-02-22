# inat.py
import requests
import json
import time
import pandas as pd

# Global cache for iNaturalist data keyed by species.
_inat_cache = {}
_last_species = None


def clear_inat_cache():
    """
    Clears the internal cache.
    """
    global _inat_cache
    _inat_cache = {}


def fetch_all_inat_data(species, use_cache=True, force=False):
    """
    Fetches all iNaturalist observations for the given species.
    If use_cache is True and force is False and data for that species is cached,
    the cached data is returned. Otherwise, a fresh API call is made.

    Returns:
        A tuple (all_results, total_obs) where:
          - all_results is a list of observation dictionaries.
          - total_obs is the total number of observations.
    """
    global _inat_cache, _last_species
    # If forced or species has changed, clear the cache.
    if force or (_last_species is None or _last_species != species):
        clear_inat_cache()
        _last_species = species

    if use_cache and species in _inat_cache:
        print(f"DEBUG: Returning cached data for species: {species}")
        return _inat_cache[species]

    inat_url = "https://api.inaturalist.org/v1/observations"
    params = {
        "taxon_name": species,
        "per_page": 200,
        "order": "asc",
        "verifiable": "true",
    }
    all_results = []
    total_obs_header = None
    page = 1

    print(f"DEBUG: Starting API calls for species: {species}")
    start_time = time.time()

    while True:
        params["page"] = page
        try:
            response = requests.get(inat_url, params=params)
            print(f"DEBUG: Requesting page {page} for species: {species}")
            if response.status_code != 200:
                print(
                    f"DEBUG: Error: Received status code {response.status_code} on page {page}"
                )
                break
            if page == 1:
                total_obs_header = int(response.headers.get("X-Total-Entries", 0))
                print(f"DEBUG: X-Total-Entries header: {total_obs_header}")
            data_page = response.json()
        except Exception as e:
            print(f"DEBUG: Exception on page {page}: {e}")
            break

        results = data_page.get("results", [])
        print(f"DEBUG: Fetched {len(results)} observations on page {page}")
        if not results:
            break
        all_results.extend(results)
        if len(results) < params["per_page"]:
            break  # No more pages available.
        page += 1

    total_obs = (
        total_obs_header
        if (total_obs_header is not None and total_obs_header > 0)
        else len(all_results)
    )
    end_time = time.time()
    print(
        f"DEBUG: Finished fetching data for species: {species} in {end_time - start_time:.2f} seconds. Total observations: {total_obs}"
    )

    _inat_cache[species] = (all_results, total_obs)
    return (all_results, total_obs)


def stream_inat_data(species, force=False):
    """
    Generator that streams progress updates while fetching iNaturalist data.
    If the data for the species is already cached and force is False, it streams a
    "CACHED" event immediately. Otherwise, it fetches data page‐by‐page, yielding
    the page number as a progress update, and finally yields a FINISHED event with all data.

    Yields:
        Strings for the client. For example:
            "1" --> indicates page 1 has been fetched.
            "FINISHED|{...}" --> indicates completion with all data.
    """
    global _inat_cache, _last_species
    if force or (_last_species is None or _last_species != species):
        clear_inat_cache()
        _last_species = species

    if species in _inat_cache:
        print(
            f"DEBUG: Data for species '{species}' found in cache. Streaming cached data."
        )
        yield f"CACHED|{json.dumps({'results': _inat_cache[species][0]})}"
        return

    inat_url = "https://api.inaturalist.org/v1/observations"
    params = {
        "taxon_name": species,
        "per_page": 200,
        "order": "asc",
        "verifiable": "true",
    }
    all_results = []
    total_obs_header = None
    page = 1

    print(f"DEBUG: Starting streaming API calls for species: {species}")
    start_time = time.time()

    while True:
        params["page"] = page
        try:
            response = requests.get(inat_url, params=params)
            print(f"DEBUG: Streaming: Requesting page {page} for species: {species}")
            if response.status_code != 200:
                yield f"ERROR: Failed to fetch page {page} (status {response.status_code})"
                break
            if page == 1:
                total_obs_header = int(response.headers.get("X-Total-Entries", 0))
                print(f"DEBUG: Streaming: X-Total-Entries header: {total_obs_header}")
            data_page = response.json()
        except Exception as e:
            yield f"ERROR: Exception on page {page}: {e}"
            break

        results = data_page.get("results", [])
        print(f"DEBUG: Streaming: Fetched {len(results)} observations on page {page}")
        yield f"{page}"
        if not results:
            break
        all_results.extend(results)
        if len(results) < params["per_page"]:
            break  # No more pages.
        page += 1

    total_obs = (
        total_obs_header
        if (total_obs_header is not None and total_obs_header > 0)
        else len(all_results)
    )
    end_time = time.time()
    print(
        f"DEBUG: Streaming: Finished fetching data for species: {species} in {end_time - start_time:.2f} seconds. Total observations: {total_obs}"
    )
    _inat_cache[species] = (all_results, total_obs)
    yield f"FINISHED|{json.dumps({'results': all_results})}"


def aggregate_inat_observations(all_results):
    """
    Aggregates monthly observation counts from iNaturalist data.

    Returns a pandas DataFrame with months 1-12 as the index and a column 'observations'.
    """
    obs_counts = {}
    for obs in all_results:
        observed_on = obs.get("observed_on")
        if observed_on:
            try:
                dt = pd.to_datetime(observed_on)
                m = dt.month
                obs_counts[m] = obs_counts.get(m, 0) + 1
            except Exception as e:
                print(f"DEBUG: Error parsing observation date '{observed_on}': {e}")
                continue
    obs_df = pd.DataFrame(
        {
            "month": list(range(1, 13)),
            "observations": [obs_counts.get(m, 0) for m in range(1, 13)],
        }
    ).set_index("month")
    return obs_df
