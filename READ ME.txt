**Herps of Greater China Climate & Distribution Explorer**  
**Version:** 8 (April 2025)

---

## Overview

The **Herps of Greater China Climate & Distribution Explorer** is a desktop/web application designed for researchers, conservationists, and wildlife enthusiasts to interactively explore reptile and amphibian species distributions alongside regional climate data in China and Taiwan. By integrating multiple open data sources, the tool provides:

- **Spatial Distribution Mapping**  
  - **iNaturalist Observations:** Live retrieval of species occurrence points from the iNaturalist API, displayed as markers on a Leaflet map.  
  - **IUCN Range Polygons:** Precise species range boundaries from the International Union for Conservation of Nature (IUCN) shapefiles, visualized as semi-transparent overlays.

- **Climate Data Analysis**  
  - **Weather Station Selection:** Dynamic loading of monthly climate data from Meteostat for any of 1,900+ stations across China and Taiwan.  
  - **Graphical Summaries:** Interactive Plotly charts combining average monthly temperature, precipitation, and relative species activity (scaled iNaturalist observations).

- **Discrepancy Reporting**  
  - Compares species lists derived from IUCN spatial data against local text files (sourced from the Reptile Database) to highlight mismatches, aiding database curation and quality control.

- **Offline & Portable**  
  - Runs as a standalone Windows executable (no Python installation required) or from source for advanced users.

---

## Data Sources

1. **iNaturalist API** (https://api.inaturalist.org)  
   Verifiable citizen-science observations, fetched page-by-page with live progress streaming.

2. **IUCN Red List Spatial Data** (https://www.iucnredlist.org)  
   - **Shapefiles**: Global reptilia polygons from the IUCN shapefile distribution dataset.  
   - **SQLite Index**: Preprocessed WKT geometries stored in `species_index.db` for fast lookup.

3. **Meteostat Climate Data** (https://meteostat.net)  
   Historical monthly temperature and precipitation for stations within the China/Taiwan bounding box.

4. **Reptile Database Text Files** (https://reptile-database.reptarium.cz)  
   Local species lists by taxonomic order (crocodilians, lizards, snakes, turtles) stored as `.txt` files in `species_files/`.

5. **Natural Earth Admin 0 – Countries** (https://www.naturalearthdata.com)  
   De facto political boundaries for deriving China/Taiwan extents, stored under `naturalearth_lowres/`.

6. **HydroBASINS Data**  
   Optional CSV-based hydrobasin information for species waterbody distributions (unused in current UI but available in `IUCN_files/reptilia_hydrobasin`).

---

## Features & Workflow

1. **Species Selection**  
   - **Dropdown**: Browse orders and species present in China/Taiwan (Reptile Database).  
   - **Global Search**: Autocomplete suggestions for any reptile species found in IUCN or local text files.

2. **Distribution Layers**  
   - **Show iNaturalist**: Dark-red point markers (90% opacity).  
   - **Show IUCN**: Red polygons (40% fill opacity), overlaid independently so both layers can be visible concurrently.

3. **Climate Station Console**  
   - Pan/zoom the map to load stations dynamically.  
   - Click up to 10 stations to view metadata (name, elevation, date range) and mini time-series charts.

4. **Graph Generation**  
   - Combine selected station climate data and aggregated monthly observations into a multi-axis Plotly graph.  
   - Display a detailed data table below the graph.

5. **Discrepancy Report**  
   - Generate side-by-side lists of species present spatially vs. those in text files, with progress streaming and manual refresh.

6. **Clear & Reset Controls**  
   - **Clear Species**: Removes both iNaturalist and IUCN layers, resets inputs.  
   - **Clear Stations**: Empties the station console and resets marker styles.

---

## Installation & Execution

### Running from Source

1. **Install Python 3.8+** and create a virtual environment (optional).  
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Launch**:
   ```bash
   python app.py
   ```
4. **Browser** opens automatically at `http://127.0.0.1:5000`.

### Running as Standalone Executable (Windows)

1. **Build** with PyInstaller (one‑folder mode):
   ```bash
   pyinstaller --noconfirm --onedir \
     --add-data "templates;templates" \
     --add-data "static;static" \
     --add-data "species_files;species_files" \
     --add-data "IUCN_files;IUCN_files" \
     --add-data "naturalearth_lowres;naturalearth_lowres" \
     --add-data "all_reptiles_world.csv;." \
     --add-data "reptiles_in_china_taiwan.csv;." \
     --add-data "reptile_discrepancy_report.txt;." \
     --add-data "species_index.db;." \
     app.py
   ```
2. **Locate** `dist/app/app.exe` and its data folders.  
3. **Zip** the entire `dist/app` folder.  
4. **Distribute** the zip; recipients unzip and double-click `app.exe`.

---

## Directory Layout for Distribution

```
Herps_Explorer/           ← your zip's root folder
├── app.exe               ← the Flask executable
├── all_reptiles_world.csv
├── reptiles_in_china_taiwan.csv
├── reptile_discrepancy_report.txt
├── species_index.db
├── templates/            ← HTML files
├── static/               ← CSS (and JS if any)
├── species_files/        ← Reptile Database text lists
├── IUCN_files/           ← shapefiles & hydrobasin CSVs
└── naturalearth_lowres/  ← Natural Earth boundary shapefiles
```

---

## Troubleshooting

- **Console closes immediately**: Run `app.exe` from a Command Prompt to view errors.  
- **Missing templates or data**: Ensure your `app.py` includes the PyInstaller path hack (`sys._MEIPASS`) and that you built with `--add-data` for all folders/files.  
- **Slow builds**: Use `--onedir` (not `--onefile`) and exclude large unused modules via `--exclude-module` flags.

---

## Acknowledgments

- **iNaturalist** community observations  
- **IUCN Red List** spatial data  
- **Meteostat** climate database  
- **Reptile Database** text species lists  
- **Natural Earth** global boundary data

---

## Contact

For questions or bug reports, please contact:
Mathew Armstrong
Email: armstrongm360@gmail.com  
GitHub: https://github.com/armstrongm360/mathew_armstrong 

Thank you for using the Climate & Distribution Explorer!  
Happy mapping and discovery!  

