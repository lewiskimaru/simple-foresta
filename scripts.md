# Foresta - Reference Scripts Documentation

## Overview

This document contains the reference scripts provided during the project's definition phase. These scripts illustrate the core logic for interacting with external APIs (OpenStreetMap, PlantNet, Google Earth Engine) and define the expected data formats (Guardian sensor data).

**Important:** These scripts are primarily for reference. Their *logic* should be integrated into the main Foresta frontend (React) and backend (Flask) applications within the appropriate services or utility functions, not necessarily run directly as standalone files (except for the sensor simulator). API keys and sensitive credentials shown here should be moved to environment variables (`.env` files) in the actual application.

---

## 1. `locationFinder.js`

*   **Purpose:** Searches the OpenStreetMap (OSM) Nominatim API for geographic locations based on a user's query and country code. This is used in the "Add New Area" feature to allow users to find and select the area they want to manage.
*   **Integration Point:** **Frontend**. The logic will be integrated into an API service function (e.g., `/src/services/osmApi.js`) called by the "Add New Area" component/modal.
*   **Input:**
    *   User search query (String, e.g., "John Michuki Memorial Park")
    *   Country code (String, e.g., "KE")
*   **Output:**
    *   Displays a list of potential location matches to the user in the UI.
    *   When a user selects a location, the frontend sends its details (name, osm\_type, osm\_id, lat, lon) to the backend. The `location-data.json` format represents the kind of data *selected* and sent.

*   **Example Output Data (`location-data.json` format - represents selected location):**

    ```json
    {
      "metadata": {
        "generated_at": "2025-04-10T18:51:22.495Z",
        "source": "OpenStreetMap Nominatim"
      },
      "locations": [
        {
          "name": "John Michuki Memorial Park, CBD division, Starehe, Nairobi, Kenya",
          "osm_type": "way",
          "osm_id": 1287470604,
          "lat": -1.27567755,
          "lon": 36.816030422381914,
          "category": "park",
          "importance": 0.08007250400549322
        }
      ]
    }
    ```

*   **Script Code:**

    ```javascript
    /*
    Location Finder Script
    ======================

    Purpose:
    --------
    This script searches for geographic locations using OpenStreetMap's Nominatim API,
    displays the results to users, and saves selected locations to a JSON file for
    later processing with boundary detection scripts.

    Key Features:
    ------------
    - Interactive search with partial name matching
    - Displays OSM metadata including coordinates and importance score
    - Allows selective saving of search results
    - Maintains search history with timestamps

    Usage:
    ------
    node locationFinder.js "Location Name" CC
    Example: node locationFinder.js "Kenyatta university" KE

    Dependencies:
    ------------
    - axios (HTTP client)
    - fs (file system)
    - readline (user input)

    Output:
    -------
    Generates 'location-data.json' with:
    - Original search parameters
    - OSM object metadata
    - Geographic coordinates
    - Search timestamp

    location-data.json
    {
      "metadata": {
        "generated_at": "2025-04-09T18:59:16.200Z",
        "source": "OpenStreetMap Nominatim"
      },
      "locations": [
        {
          "name": "Location name",
          "osm_type": "relation",
          "osm_id": 185567,
          "lat": -1.45056,
          "lon": -48.4682453,
          "category": "administrative",
          "importance": 0.604294926580297
        }
      ]
    }

    Data Source:
    -----------
    OpenStreetMap (https://www.openstreetmap.org)
    */

    const axios = require('axios');
    const fs = require('fs');
    const readline = require('readline');

    // Configure API client with proper user agent
    axios.defaults.headers.common['User-Agent'] = 'GeoFinder/1.0 (kamau.kimaru1@students.jkuat.ac.ke)'; // Use a relevant agent for the Foresta App

    // Set up interactive console interface (NOTE: In React, this will be UI elements)
    const rl = readline.createInterface({
      input: process.stdin,
      output: process.stdout
    });

    /**
     * Search OpenStreetMap for locations matching query
     * @param {string} query - Location name to search
     * @param {string} countryCode - 2-letter country code filter
     * @returns {Promise<Array>} Array of location objects or null on error
     */
    async function searchLocations(query, countryCode) {
      try {
        const response = await axios.get('https://nominatim.openstreetmap.org/search', {
          params: {
            q: query,
            countrycodes: countryCode,
            format: 'jsonv2',
            addressdetails: 1, // Get address details
            limit: 5 // Limit results
          }
        });

        // Map to desired format
        return response.data.map(item => ({
          name: item.display_name,
          osm_type: item.osm_type,
          osm_id: item.osm_id,
          lat: parseFloat(item.lat),
          lon: parseFloat(item.lon),
          category: item.category, // Use 'category' instead of 'type' from jsonv2
          importance: item.importance
        }));

      } catch (error) {
        console.error('Search failed:', error.response ? error.response.data : error.message);
        // In React, you would handle this error state in the UI
        return null;
      }
    }

    /**
     * Save selected locations to JSON file (NOTE: In React, this sends data to backend)
     * @param {Array} data - Array of location objects to save/send
     */
    async function saveLocationData(data) {
      const jsonData = {
        metadata: {
          generated_at: new Date().toISOString(),
          source: "OpenStreetMap Nominatim"
        },
        locations: data // In React, you'd likely send just the selected location object
      };

      // This file writing is for the script's original purpose.
      // In the webapp, this step is replaced by sending the selected data to the backend API.
      fs.writeFileSync('location-data.json', JSON.stringify(jsonData, null, 2));
      console.log('\n✅ Reference: Saved location data to location-data.json');
    }

    /**
     * Main workflow controller (Illustrative command-line usage)
     */
    async function main() {
      const args = process.argv.slice(2);
      if (args.length < 2) {
        console.log('Usage: node locationFinder.js "Location Name" CC');
        process.exit(1);
      }

      const results = await searchLocations(args[0], args[1].toUpperCase());
      if (!results || results.length === 0) {
        console.log('No results found');
        process.exit(1); // In React, show "No results" message
      }

      // Display formatted results (In React, render this list in the UI)
      console.log('\n📋 Search Results:');
      results.forEach((loc, index) => {
        console.log(`${index + 1}. ${loc.name}`);
        console.log(`   OSM Type: ${loc.osm_type} (Category: ${loc.category})`); // Adjusted field name
        console.log(`   Coordinates: ${loc.lat.toFixed(6)}, ${loc.lon.toFixed(6)}`);
        console.log(`   Importance: ${loc.importance.toFixed(2)}\n`);
      });

      // Handle user selection (In React, this is done via onClick handlers)
      rl.question('\nEnter numbers to save (comma-separated, or "all"): ', answer => {
        const indices = answer.toLowerCase() === 'all'
          ? results.map((_, i) => i)
          : answer.split(',').map(num => parseInt(num.trim()) - 1).filter(n => !isNaN(n) && n >= 0 && n < results.length);

        const selectedLocations = indices.map(index => results[index]);

        if (selectedLocations.length > 0) {
           // In the web app context, you would typically select only *one* location
           // and send that single location's data {name, osm_type, osm_id, lat, lon}
           // to the backend API upon confirmation (e.g., clicking a "Confirm Area" button).
           console.log("\nSelected Location(s) for reference saving:");
           console.log(selectedLocations);
           saveLocationData(selectedLocations); // Save for reference, app sends data to backend
        } else {
           console.log("No valid selections made.");
        }
        rl.close();
      });
    }

    // Start application if run directly
    if (require.main === module) {
        main();
    }
    ```

---

## 2. `boundary_finder.py`

*   **Purpose:** Fetches the detailed geographic boundary coordinates (polygon data) for a specific location using its OSM ID and Type via the OSM Overpass API. This happens *after* a user selects a location found via `locationFinder.js`.
*   **Integration Point:** **Backend**. The logic will be integrated into a service function (e.g., `/app/services/osm_service.py`) called by the `/api/areas` endpoint when creating a new area.
*   **Input:**
    *   Location details (OSM ID, OSM Type) received from the frontend API request. Conceptually, this comes from the selected item in `location-data.json`.
*   **Output:**
    *   A list of coordinate pairs `[[latitude, longitude], ...]` representing the boundary.
    *   This coordinate list is saved into the `boundary_coordinates` column of the `Areas` table in the database. The `boundaries.json` format represents this output data structure.

*   **Example Input Data (Conceptually from `location-data.json` selection):**
    *   `osm_id`: 1287470604
    *   `osm_type`: "way"

*   **Example Output Data (`boundaries.json` format - represents data stored in DB):**

    ```json
    {
      "metadata": {
        "source": "OpenStreetMap",
        "generated_at": "2025-04-10T18:51:26.425545"
      },
      "boundaries": {
        "John Michuki Memorial Park, CBD division, Starehe, Nairobi, Kenya": [
          [
            -1.2747409,
            36.8127541
          ],
          [
            -1.2748443,
            36.8127784
          ],
          // ... many more coordinates ...
          [
            -1.2728837,
            36.8154122
          ]
        ]
      }
    }
    ```
    *(Note: In the database, only the array of coordinates for the specific area would be stored, likely in a TEXT or JSON field, associated with the area record.)*

*   **Script Code:**

    ```python
    """
    Boundary Finder Script
    ======================

    Purpose:
    --------
    This script processes geographic locations from a JSON file and fetches their
    boundary coordinates using OpenStreetMap's Overpass API. It handles nodes, ways,
    and relations to provide comprehensive geographic data for analysis.

    Key Features:
    ------------
    - Processes locations from JSON input file
    - Supports all OSM element types (nodes, ways, relations)
    - Handles complex multi-polygon relationships
    - Generates structured boundary files with metadata
    - Provides error handling and progress reporting

    Usage:
    ------
    1. First run locationFinder.js to generate location-data.json
    2. Then run: python boundary_finder.py (for reference)
       (In the webapp, this logic is triggered by the backend API)

    Dependencies:
    ------------
    - requests (HTTP client)
    - datetime (timestamp generation)
    - typing (type annotations)

    Output:
    -------
    Generates 'boundaries.json' with:
    - Full coordinate sets for each location
    - Source metadata and generation timestamp
    - Structured by location name

    boundaries.json
    {
      "metadata": {
        "source": "OpenStreetMap",
        "generated_at": "<ISO 8601 timestamp>"
      },
      "boundaries": {
        "<location_name>": [
          [<latitude>, <longitude>],
          ...
        ],
        ...
      }
    }

    Data Sources:
    ------------
    - Input: location-data.json (from Nominatim API) - Conceptual input for the backend logic
    - Boundaries: OpenStreetMap Overpass API
    """

    import requests
    import json
    from datetime import datetime
    from typing import List, Dict, Optional, Any
    import time # Added for potential rate limiting delays

    # In the backend service, the location file path would not be hardcoded.
    # The function would receive osm_id and osm_type as parameters.
    DEFAULT_LOCATION_FILE = 'location-data.json' # Reference input
    DEFAULT_OUTPUT_FILE = 'boundaries.json' # Reference output

    class BoundaryFinder:
        """
        Main class for fetching and processing geographic boundaries.
        In the backend, this might be refactored into service functions.

        Attributes:
            base_url: Overpass API endpoint
        """

        def __init__(self):
            """Initialize with Overpass API endpoint."""
            self.base_url = "https://overpass-api.de/api/interpreter"
            # User agent should be specific to the Foresta application
            self.headers = {
                'Content-Type': 'text/plain',
                'User-Agent': 'ForestaApp/1.0 (Backend Service; contact@example.com)' # Replace with actual contact
            }

        def _load_locations(self, file_path: str) -> List[Dict]:
            """
            Load and validate location data from JSON file (Reference script usage).
            In backend, this data comes from the API request payload.
            """
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                locations = data.get('locations', [])
                if not locations:
                    print(f"Warning: No locations found in {file_path}")
                return locations
            except (FileNotFoundError, json.JSONDecodeError) as e:
                print(f"Error loading locations from {file_path}: {str(e)}")
                return []
            except Exception as e:
                 print(f"An unexpected error occurred loading {file_path}: {str(e)}")
                 return []

        def _build_query(self, osm_type: str, osm_id: int) -> str:
            """
            Construct Overpass QL query for specific OSM object.
            """
            osm_type_lower = osm_type.lower()
            if osm_type_lower not in ['node', 'way', 'relation']:
                raise ValueError(f"Invalid OSM type: {osm_type}")

            # Query to get the geometry of the specified element and its descendants
            return f"""
            [out:json][timeout:25];
            (
              {osm_type_lower}({osm_id});
            );
            (._;>;);
            out geom;
            """

        def _process_element(self, element: Dict) -> List[List[float]]:
            """
            Extract coordinates from a single OSM API response element.
            Returns coordinates as [latitude, longitude].
            """
            coords = []
            element_type = element.get('type')

            if element_type == 'node':
                # Nodes have explicit lat/lon
                if 'lat' in element and 'lon' in element:
                    coords.append([element['lat'], element['lon']])
            elif element_type in ['way', 'relation']:
                 # Ways and Relations might have a 'geometry' array of nodes
                 # Or relations might have members which themselves have geometry
                if 'geometry' in element and element['geometry']:
                    # Geometry is typically [lon, lat] in GeoJSON-like outputs, but Overpass geom is list of nodes
                    # Ensure the nodes have lat/lon
                    coords.extend([[node['lat'], node['lon']] for node in element['geometry'] if 'lat' in node and 'lon' in node])
                elif 'members' in element:
                    # Handle relation members recursively? No, Overpass `out geom` should resolve this.
                    # If a relation member is returned *without* geometry, it might be complex.
                    # The `(._;>;); out geom;` query aims to resolve member geometries.
                    # We might only get coordinates if the element itself is a way OR if the relation members were resolved to ways with geometry.
                     pass # Geometry should have been fetched by the query

            return coords

        def _extract_coordinates_from_response(self, response_data: Dict) -> List[List[float]]:
            """
            Extract all coordinate pairs from the full Overpass API response.
            Prioritizes ways and relations over nodes if multiple element types are returned.
            """
            all_coords = []
            elements = response_data.get('elements', [])

            # Separate elements by type
            nodes = [el for el in elements if el.get('type') == 'node']
            ways = [el for el in elements if el.get('type') == 'way']
            relations = [el for el in elements if el.get('type') == 'relation']

            # Prioritize ways, then relations, then nodes for geometry
            processed_elements = ways + relations + nodes

            for element in processed_elements:
                 coords = self._process_element(element)
                 if coords:
                     # If we found coords (likely from a way or resolved relation), use them and stop for this element group
                     all_coords.extend(coords)
                     # Optimization: If we got coordinates from a way/relation that matches the requested ID,
                     # we might not need coordinates from individual nodes unless it's a point feature.
                     # For simplicity here, we collect all valid coordinates found.
                     # A more sophisticated approach might be needed for complex relations.

            # Simple deduplication based on exact lat/lon string representation
            if all_coords:
                 unique_coords_set = set(f"{lat},{lon}" for lat, lon in all_coords)
                 all_coords = [[float(p.split(',')[0]), float(p.split(',')[1])] for p in unique_coords_set]


            return all_coords


        def fetch_boundary(self, osm_type: str, osm_id: int) -> Optional[List[List[float]]]:
            """
            Fetch boundaries for a single location.
            """
            try:
                print(f"Fetching boundary for {osm_type} {osm_id}...")
                query = self._build_query(osm_type, osm_id)
                response = requests.post(
                    self.base_url,
                    data=query,
                    headers=self.headers,
                    timeout=30 # Increased timeout for potentially complex queries
                )
                response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)

                data = response.json()
                coordinates = self._extract_coordinates_from_response(data)

                if not coordinates:
                     print(f"Warning: No coordinates extracted for {osm_type} {osm_id}. Response might be empty or lack geometry.")
                     # Fallback: Could try fetching the center coordinates if available?
                     center_coords = self._find_center_coords(data, osm_id)
                     if center_coords:
                         print("Using center coordinates as a fallback point.")
                         return [center_coords] # Return as a single point list
                     return None # Indicate failure to get boundary

                print(f"Successfully fetched {len(coordinates)} coordinate points for {osm_type} {osm_id}.")
                return coordinates

            except requests.exceptions.RequestException as e:
                print(f"Network or HTTP error fetching boundary for {osm_type} {osm_id}: {str(e)}")
                return None
            except ValueError as e:
                 print(f"Data processing error for {osm_type} {osm_id}: {str(e)}")
                 return None
            except Exception as e:
                print(f"An unexpected error occurred for {osm_type} {osm_id}: {str(e)}")
                return None

        def _find_center_coords(self, response_data: Dict, target_id: int) -> Optional[List[float]]:
            """Helper to find center coordinates if geometry is missing, especially for relations."""
            elements = response_data.get('elements', [])
            for element in elements:
                if element.get('id') == target_id and 'center' in element:
                    center = element['center']
                    if 'lat' in center and 'lon' in center:
                        return [center['lat'], center['lon']]
            return None


        def process_locations_from_file(self, location_file: str = DEFAULT_LOCATION_FILE) -> Dict[str, Optional[List[List[float]]]]:
            """
            Fetch boundaries for all locations in the input file (Reference script usage).
            """
            locations = self._load_locations(location_file)
            results = {}
            if not locations:
                 print("No locations to process.")
                 return results

            for i, location in enumerate(locations):
                name = location.get('name', f"Unnamed Location {i+1}")
                osm_id = location.get('osm_id')
                osm_type = location.get('osm_type')

                if osm_id is None or osm_type is None:
                    print(f"Skipping location '{name}': Missing osm_id or osm_type.")
                    results[name] = None
                    continue

                coordinates = self.fetch_boundary(osm_type, osm_id)
                results[name] = coordinates

                # Add a small delay to respect Overpass API usage policies
                if i < len(locations) - 1: # Don't sleep after the last one
                    time.sleep(2) # 2-second delay between requests

            return results

        def save_results(self, boundaries: Dict[str, Optional[List[List[float]]]], output_file: str = DEFAULT_OUTPUT_FILE):
            """
            Save processed boundaries to JSON file (Reference script usage).
            """
            # Filter out entries where boundary fetching failed (value is None)
            valid_boundaries = {name: coords for name, coords in boundaries.items() if coords is not None}

            output_data = {
                "metadata": {
                    "source": "OpenStreetMap Overpass API",
                    "generated_at": datetime.now().isoformat()
                },
                "boundaries": valid_boundaries # Save only successfully fetched boundaries
            }
            try:
                with open(output_file, 'w') as f:
                    json.dump(output_data, f, indent=2)
                print(f"Boundary data saved to {output_file}")
                print(f"Successfully saved boundaries for {len(valid_boundaries)} out of {len(boundaries)} locations.")
            except IOError as e:
                print(f"Error saving results to {output_file}: {str(e)}")
            except Exception as e:
                print(f"An unexpected error occurred during saving: {str(e)}")


    if __name__ == "__main__":
        """Command-line execution entry point for reference script"""
        finder = BoundaryFinder()
        # In the webapp, you would call finder.fetch_boundary(type, id) directly.
        # The file processing part below is just for the reference script's operation.
        processed_boundaries = finder.process_locations_from_file()

        if processed_boundaries:
            finder.save_results(processed_boundaries)

            # Example output for verification
            first_valid_boundary = next(((name, coords) for name, coords in processed_boundaries.items() if coords), None)
            if first_valid_boundary:
                name, coords = first_valid_boundary
                print(f"\nSample coordinates for {name} (first 5 points):")
                print(json.dumps(coords[:5], indent=2))
            else:
                 print("\nNo valid boundaries were fetched to show a sample.")
        else:
             print("\nNo boundaries were processed.")

    ```

---

## 3. `gee.py`

*   **Purpose:** Uses the Google Earth Engine (GEE) Python API to calculate forest change statistics (tree loss %, tree gain %, annual deforestation trends) for a given geographic area defined by boundary coordinates.
*   **Integration Point:** **Backend**. The logic will be integrated into a service function (e.g., `/app/services/gee_service.py`) likely called asynchronously or on-demand after an area is created or when its details are requested.
*   **Input:**
    *   Boundary coordinates (List of `[latitude, longitude]` pairs, fetched from the `Areas` database table). Conceptually represented by `boundaries.json`.
    *   GEE Service Account Credentials (`foresta-456412-17f5747ef974.json` - path configured in backend `.env`).
*   **Output:**
    *   A dictionary containing the calculated metrics: `tree_loss_percentage`, `tree_gain_percentage`, `deforestation_trends` (dict mapping year string to loss in hectares).
    *   These results are saved into the corresponding columns of the `Areas` table in the database. The `area_sat.json` format represents this output data structure.

*   **Example Input Data (`boundaries.json` format - defines the geometry):**

    ```json
    {
      "metadata": {
        "source": "OpenStreetMap",
        "generated_at": "2025-04-10T18:51:26.425545"
      },
      "boundaries": {
        "John Michuki Memorial Park, CBD division, Starehe, Nairobi, Kenya": [
          [ -1.2747409, 36.8127541 ],
          [ -1.2748443, 36.8127784 ],
          // ... many more coordinates ...
          [ -1.2728837, 36.8154122 ]
        ]
      }
    }
    ```

*   **Example Input Credentials (`foresta-456412-17f5747ef974.json`):**

    ```json
    {
      "type": "service_account",
      "project_id": "foresta-456412",
      "private_key_id": "17f5747ef9741af1474dc1e0b23619999993bd09",
      "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n",
      "client_email": "school@foresta-456412.iam.gserviceaccount.com",
      "client_id": "104423134552772420352",
      "auth_uri": "https://accounts.google.com/o/oauth2/auth",
      "token_uri": "https://oauth2.googleapis.com/token",
      "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
      "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/school%40foresta-456412.iam.gserviceaccount.com",
      "universe_domain": "googleapis.com"
    }

    ```

*   **Example Output Data (`area_sat.json` format - represents data stored in DB):**

    ```json
    [
      {
        "area": "John Michuki Memorial Park, CBD division, Starehe, Nairobi, Kenya",
        "tree_loss_percentage": 36.74149708491336,
        "tree_gain_percentage": 0,
        "deforestation_trends": {
          "2001": 0.26812790527343755,
          "2002": 0,
          "2003": 0,
          "2004": 0,
          "2005": 0,
          "2006": 0,
          "2007": 0,
          "2008": 0,
          "2009": 0,
          "2010": 0.020679141869638484,
          "2011": 0,
          "2012": 0,
          "2013": 0,
          "2014": 0,
          "2015": 0,
          "2016": 0,
          "2017": 0,
          "2018": 0,
          "2019": 0,
          "2020": 0.2905594862515319,
          "2021": 0,
          "2022": 0,
          "2023": 0
        }
      }
    ]
    ```
    *(Note: In the database, these metrics would be stored in columns of the `Areas` table for the specific area.)*

*   **Script Code:**

    ```python
    #!/usr/bin/env python3
    """
    Forest Change Analyzer using Google Earth Engine (Reference Script)

    Description:
    Calculates forest change metrics (tree loss/gain percentages and annual deforestation trends)
    for specified geographic areas using the Hansen Global Forest Change dataset.

    Integration:
    The core logic of `compute_forest_change` will be adapted into a backend service function.
    This function will take boundary coordinates (List[List[float]]) as input,
    authenticate using credentials from environment variables, perform GEE computations,
    and return the results dictionary to be stored in the database.

    Dependencies:
    - earthengine-api
    - json (standard library)

    Authentication:
    Relies on service account credentials specified by environment variables in the backend.
    SERVICE_ACCOUNT = os.environ.get('GEE_SERVICE_ACCOUNT_EMAIL')
    KEY_FILE = os.environ.get('GEE_KEY_FILE_PATH')
    """

    import ee
    import json
    import os
    from typing import List, Dict, Any, Tuple

    # --- Constants ---
    # In the backend service, these would come from environment variables or config
    DEFAULT_SERVICE_ACCOUNT = 'school@foresta-456412.iam.gserviceaccount.com' # Example
    DEFAULT_KEY_FILE = 'foresta-456412-17f5747ef974.json' # Example, path relative to script/config
    DEFAULT_INPUT_FILE = 'boundaries.json' # Reference input
    DEFAULT_OUTPUT_FILE = 'area_sat.json' # Reference output
    GFC_DATASET = 'UMD/hansen/global_forest_change_2023_v1_11'
    FOREST_THRESHOLD = 30 # Minimum % tree cover to be considered forest in 2000
    GEOMETRY_SCALE = 30 # Scale in meters for reductions (matches Hansen dataset resolution)
    MAX_PIXELS = 1e13 # Max pixels for reduceRegion operations

    # --- GEE Initialization ---
    _gee_initialized = False

    def initialize_gee():
        """Initializes Earth Engine API using service account credentials."""
        global _gee_initialized
        if _gee_initialized:
            return True

        service_account = os.environ.get('GEE_SERVICE_ACCOUNT_EMAIL', DEFAULT_SERVICE_ACCOUNT)
        key_file = os.environ.get('GEE_KEY_FILE_PATH', DEFAULT_KEY_FILE) # Path should be absolute or relative to backend root

        if not service_account or not key_file:
            print("Error: GEE_SERVICE_ACCOUNT_EMAIL or GEE_KEY_FILE_PATH not set in environment/config.")
            return False

        if not os.path.exists(key_file):
             print(f"Error: GEE key file not found at path: {key_file}")
             # Attempt path relative to this script file (useful for standalone execution)
             script_dir = os.path.dirname(__file__)
             alt_key_path = os.path.join(script_dir, '..', 'important_scripts', 'data_artifacts', os.path.basename(key_file)) # Example adjustment
             if os.path.exists(alt_key_path):
                  print(f"Attempting alternative path: {alt_key_path}")
                  key_file = alt_key_path
             else:
                  alt_key_path_2 = os.path.join(script_dir, os.path.basename(key_file))
                  if os.path.exists(alt_key_path_2):
                      print(f"Attempting alternative path: {alt_key_path_2}")
                      key_file = alt_key_path_2
                  else:
                      print("Could not find key file.")
                      return False


        try:
            print(f"Initializing GEE with Service Account: {service_account} and Key File: {key_file}")
            credentials = ee.ServiceAccountCredentials(service_account, key_file)
            # Specify project ID if needed, helps avoid ambiguity
            project_id = service_account.split('@')[1].split('.')[0] if '@' in service_account else 'foresta-456412' # Extract from email or use default
            ee.Initialize(credentials, project=project_id, opt_url='https://earthengine-highvolume.googleapis.com')
            print(f"GEE Initialized Successfully. Project: {project_id}")
            _gee_initialized = True
            return True
        except ee.EEException as e:
            print(f"GEE Initialization Failed: {e}")
            return False
        except Exception as e:
             print(f"An unexpected error occurred during GEE initialization: {e}")
             return False


    def get_gee_area_name_info(geometry: ee.Geometry) -> Dict[str, str]:
        """
        Attempts to find administrative area names intersecting the geometry.
        Returns a dictionary of names found.
        """
        names_info = {"level0": "Not Found", "level1": "Not Found", "level2": "Not Found"}
        if not _gee_initialized: return names_info

        try:
            # Use FAO GAUL datasets
            gaul_l0 = ee.FeatureCollection('FAO/GAUL/2015/level0')
            gaul_l1 = ee.FeatureCollection('FAO/GAUL/2015/level1')
            gaul_l2 = ee.FeatureCollection('FAO/GAUL/2015/level2')

            # Filter features intersecting the geometry centroid for efficiency
            centroid = geometry.centroid(maxError=1) # maxError for performance
            intersect_l0 = gaul_l0.filterBounds(centroid)
            intersect_l1 = gaul_l1.filterBounds(centroid)
            intersect_l2 = gaul_l2.filterBounds(centroid)

            # Helper to get names safely
            def get_name(fc: ee.FeatureCollection, prop: str) -> str:
                try:
                    # Get the first intersecting feature's name
                    feature = fc.first()
                    name = ee.Algorithms.If(feature, feature.get(prop), "Not Found").getInfo()
                    return name if name else "Not Found"
                except Exception:
                     # Handle cases where getInfo() might fail on empty collections etc.
                     return "Error retrieving"


            names_info["level0"] = get_name(intersect_l0, 'ADM0_NAME')
            names_info["level1"] = get_name(intersect_l1, 'ADM1_NAME')
            names_info["level2"] = get_name(intersect_l2, 'ADM2_NAME')

        except ee.EEException as e:
            print(f"GEE Error in get_gee_area_name_info: {e}")
        except Exception as e:
            print(f"Unexpected Error in get_gee_area_name_info: {e}")

        return names_info


    def compute_forest_change(area_name: str, geometry: ee.Geometry) -> Optional[Dict[str, Any]]:
        """
        Compute forest change metrics for a given geometry using GEE.

        Args:
            area_name (str): Name of the area (for context).
            geometry (ee.Geometry): Geometry object defining the area boundaries.

        Returns:
            dict: Dictionary containing metrics or None on failure.
        """
        if not initialize_gee(): # Ensure GEE is initialized
             return None

        print(f"\nProcessing GEE analysis for area: {area_name}")

        try:
            # --- Optional: Get GEE administrative names for logging ---
            # name_info = get_gee_area_name_info(geometry)
            # print(f"  Informational GEE Name Lookup: L0={name_info['level0']}, L1={name_info['level1']}, L2={name_info['level2']}")
            # ---

            # Load the Hansen Global Forest Change dataset
            gfc = ee.Image(GFC_DATASET)

            # Define forest cover in 2000 (using the specified threshold)
            tree_cover_2000 = gfc.select('treecover2000')
            initial_forest_mask = tree_cover_2000.gte(FOREST_THRESHOLD) # Mask: 1 where forest, 0 otherwise

            # Calculate total area of the geometry in hectares
            pixel_area_ha = ee.Image.pixelArea().divide(10000) # Area per pixel in hectares
            total_area_stat = pixel_area_ha.reduceRegion(
                reducer=ee.Reducer.sum(),
                geometry=geometry,
                scale=GEOMETRY_SCALE,
                maxPixels=MAX_PIXELS
            )
            total_area_ha = ee.Number(total_area_stat.get('area')) # Total hectares

            # Calculate initial forest area in hectares
            initial_forest_area = initial_forest_mask.multiply(pixel_area_ha)
            initial_forest_stat = initial_forest_area.reduceRegion(
                reducer=ee.Reducer.sum(),
                geometry=geometry,
                scale=GEOMETRY_SCALE,
                maxPixels=MAX_PIXELS
            )
            initial_forest_ha = ee.Number(initial_forest_stat.get('treecover2000')) # Hectares of forest in 2000

            # Calculate total loss area (only within areas that were forest in 2000)
            loss_mask = gfc.select('loss').And(initial_forest_mask) # Loss where it was forest
            loss_area = loss_mask.multiply(pixel_area_ha)
            loss_stat = loss_area.reduceRegion(
                reducer=ee.Reducer.sum(),
                geometry=geometry,
                scale=GEOMETRY_SCALE,
                maxPixels=MAX_PIXELS
            )
            loss_total_ha = ee.Number(loss_stat.get('loss'))

            # Calculate loss percentage relative to initial forest cover
            loss_percentage = ee.Algorithms.If(
                initial_forest_ha.gt(0),
                loss_total_ha.divide(initial_forest_ha).multiply(100),
                0 # Avoid division by zero if no initial forest
            )

            # Calculate total gain area (gain happens in non-forest areas)
            gain_mask = gfc.select('gain')#.And(initial_forest_mask.Not()) # Gain only where it wasn't forest? Definition varies. GFC gain is where non-forest became forest.
            gain_area = gain_mask.multiply(pixel_area_ha)
            gain_stat = gain_area.reduceRegion(
                reducer=ee.Reducer.sum(),
                geometry=geometry,
                scale=GEOMETRY_SCALE,
                maxPixels=MAX_PIXELS
            )
            gain_total_ha = ee.Number(gain_stat.get('gain'))

            # Calculate gain percentage relative to the *total* area
            gain_percentage = ee.Algorithms.If(
                total_area_ha.gt(0),
                 gain_total_ha.divide(total_area_ha).multiply(100),
                 0 # Avoid division by zero
            )

            # Calculate annual deforestation trends (loss per year in hectares)
            lossyear_band = gfc.select('lossyear') # Band values 1-23 correspond to 2001-2023
            years = ee.List.sequence(1, 23)

            def compute_annual_loss(year_num: ee.Number) -> ee.Dictionary:
                year_num = ee.Number(year_num) # Cast just in case
                # Loss in this year AND where it was initially forest
                annual_loss_mask = lossyear_band.eq(year_num).And(initial_forest_mask)
                annual_loss_area = annual_loss_mask.multiply(pixel_area_ha)
                loss_sum_stat = annual_loss_area.reduceRegion(
                    reducer=ee.Reducer.sum(),
                    geometry=geometry,
                    scale=GEOMETRY_SCALE,
                    maxPixels=MAX_PIXELS
                )
                loss_sum_ha = ee.Number(loss_sum_stat.get('lossyear')).unmask(0) # Default to 0 if no loss
                # Return dictionary with year string and loss value
                return ee.Dictionary({'year': year_num.add(2000).format('%d'), 'loss_ha': loss_sum_ha})

            # Map over the years and get results as a list of dictionaries
            annual_loss_list = years.map(compute_annual_loss)

            # Convert the list of dictionaries into a single dictionary { 'year_str': loss_ha }
            # Need to getInfo() to do this manipulation in Python
            annual_loss_info = annual_loss_list.getInfo()
            deforestation_trends_dict = {item['year']: item['loss_ha'] for item in annual_loss_info}


            # Get final values (server-side objects -> Python types)
            # Use getInfo() to retrieve the computed values
            results = {
                "area": area_name, # Include name for reference
                "tree_loss_percentage": loss_percentage.getInfo(),
                "tree_gain_percentage": gain_percentage.getInfo(),
                "deforestation_trends": deforestation_trends_dict
            }
            print(f"GEE analysis complete for {area_name}.")
            return results

        except ee.EEException as e:
            print(f"GEE Error during computation for {area_name}: {e}")
            return None
        except Exception as e:
            print(f"Unexpected Error during computation for {area_name}: {e}")
            return None


    # --- Main execution block (for reference script usage) ---
    if __name__ == "__main__":
        print("Running GEE Analysis Reference Script...")

        # Load boundaries from the input JSON file
        input_file = DEFAULT_INPUT_FILE
        if not os.path.exists(input_file):
             # Try alternative path relative to script
             script_dir = os.path.dirname(__file__)
             input_file = os.path.join(script_dir, '..', 'important_scripts', 'data_artifacts', os.path.basename(input_file))
             if not os.path.exists(input_file):
                  print(f"Error: Input boundaries file not found at {DEFAULT_INPUT_FILE} or {input_file}")
                  exit(1)


        try:
             with open(input_file, 'r') as f:
                 data = json.load(f)
        except Exception as e:
             print(f"Error reading input file {input_file}: {e}")
             exit(1)

        # Process each area in the boundaries dictionary
        results_list = []
        if 'boundaries' not in data or not isinstance(data['boundaries'], dict):
             print(f"Error: Input file {input_file} does not contain a 'boundaries' dictionary.")
             exit(1)

        for area_name, coordinates in data['boundaries'].items():
            if not coordinates or not isinstance(coordinates[0], list) or len(coordinates[0]) != 2:
                 print(f"Skipping area '{area_name}': Invalid coordinates format.")
                 continue

            # Convert coordinates from [lat, lon] (expected input) to [lon, lat] for ee.Geometry.Polygon
            try:
                 ee_coords = [[lon, lat] for [lat, lon] in coordinates]
            except Exception as e:
                 print(f"Skipping area '{area_name}': Error processing coordinates - {e}")
                 continue

            # Create an Earth Engine geometry
            try:
                 geometry = ee.Geometry.Polygon(ee_coords)
            except ee.EEException as e:
                 print(f"Skipping area '{area_name}': Error creating GEE geometry - {e}")
                 continue

            # Compute forest change metrics
            result = compute_forest_change(area_name, geometry)
            if result:
                 results_list.append(result)

        # Write results to output JSON file
        output_file = DEFAULT_OUTPUT_FILE
        try:
             with open(output_file, 'w') as f:
                 json.dump(results_list, f, indent=2)
             print(f"\nReference results written to {output_file}")
        except IOError as e:
             print(f"Error writing output file {output_file}: {e}")

        # Optional: Print results for verification
        print("\n--- Summary ---")
        if results_list:
            for result in results_list:
                print(f"Area: {result['area']}")
                print(f"  Tree Loss Percentage: {result['tree_loss_percentage']:.2f}%")
                print(f"  Tree Gain Percentage: {result['tree_gain_percentage']:.2f}%")
                print("  Deforestation Trends (ha):")
                # Print only a few years for brevity
                trends = result['deforestation_trends']
                years_to_show = list(trends.keys())[:3] + ['...'] + list(trends.keys())[-3:] if len(trends) > 6 else list(trends.keys())
                for year in years_to_show:
                     if year == '...': print(f"    ...")
                     else: print(f"    {year}: {trends.get(year, 0):.2f}")
                print("-" * 10)
        else:
             print("No results were generated.")
    ```

---

## 4. `plantnet.js`

*   **Purpose:** Identifies plant species by sending user-uploaded images to the PlantNet API. It processes the API response to extract key information.
*   **Integration Point:** **Frontend**. The logic will be integrated into an API service function (e.g., `/src/services/plantnetApi.js`) called directly from the "Species ID" page component when a user uploads an image.
*   **Input:**
    *   Image file(s) uploaded by the user (up to 5).
    *   PlantNet API Key (from frontend `.env` variable `VITE_PLANTNET_API_KEY`).
*   **Output:**
    *   Displays the identification results (JSON format, potentially styled) to the user on the Species ID page.
    *   Sends the full JSON result and the URL of the uploaded image (after storing it, e.g., in a folder on the project directory or similar) to the backend API (`/api/areas/<area_id>/species`) to be saved in the `SpeciesIdentifications` database table. The `species.json` format represents the data structure of the result.

*   **Example Input Data:**
    *   An image file (e.g., `hibiscus.jpg`).

*   **Example Output Data (`species.json` format - represents result displayed and sent to backend):**

    ```json
    {
      "timestamp": "2025-04-10T16:52:25.309Z",
      "apiVersion": "2025-01-17 (7.3)",
      "bestMatch": "Hibiscus rosa-sinensis L.",
      "results": [
        {
          "score": 0.76963,
          "taxonomy": {
            "scientificName": "Hibiscus rosa-sinensis",
            "genus": "Hibiscus",
            "family": "Malvaceae"
          },
          "commonNames": [
            "Hawaiian hibiscus",
            "Hibiscus",
            "गुड़हल"
          ],
          "conservation": {
            "status": "Not assessed",
            "source": null
          },
          "references": {
            "gbif": "3152559",
            "powo": "560756-1"
          }
        }
        // Script originally sliced to top 1, but API might return more.
        // Webapp could potentially show more than just the first result.
      ],
      "remainingRequests": 487 // Provided by PlantNet API
    }
    ```

*   **Script Code:**

    ```javascript
    'use strict';

    /**
     * PlantNet Species Identification and Data Export Script (Reference)
     *
     * Description:
     * This script identifies plant species using PlantNet's API and exports results in a concise JSON format.
     * It handles image processing, API communication, and data simplification for efficient storage.
     *
     * Integration:
     * The core logic of `identifyPlant` and `processResults` will be adapted into frontend service functions.
     * The frontend component will handle file input, call the service function, display results,
     * and send the processed results (+ image reference) to the backend for storage.
     *
     * API Key: Should be stored securely in frontend environment variables (e.g., VITE_PLANTNET_API_KEY).
     * Dependencies (for webapp): axios, FormData (built-in).
     */

    const fs = require('fs'); // Used in script, not directly in frontend (use File object)
    const axios = require('axios'); // Use in frontend
    const FormData = require('form-data'); // Use browser's FormData in frontend

    // ======================
    // CONFIGURATION (Examples - Use Environment Variables in App)
    // ======================
    const API_KEY = process.env.VITE_PLANTNET_API_KEY || '2b10VlJv3mzvHM3Lkhb9r06cSO'; // Get from env
    const PROJECT = 'all'; // Identification project: 'all' for global database
    const MAX_IMAGES = 5; // API limit for concurrent image processing
    const PLANTNET_API_URL = `https://my-api.plantnet.org/v2/identify/${PROJECT}`;

    // ======================
    // CORE FUNCTIONALITY (Adapt for Frontend Service)
    // ======================

    /**
     * Plant Identification Handler (Frontend Adaptation)
     * @param {string} apiKey - PlantNet API credentials
     * @param {FileList | File[]} imageFiles - Array/List of File objects from input
     * @returns {Promise<Object>} Raw API response data from PlantNet
     * @throws {Error} On API errors or invalid input
     */
    async function identifyPlant(apiKey, imageFiles) {
      // Input validation
      if (!imageFiles || imageFiles.length === 0) throw new Error('No image files provided');
      if (imageFiles.length > MAX_IMAGES) {
        throw new Error(`API limit: Maximum ${MAX_IMAGES} images per request. You provided ${imageFiles.length}.`);
      }

      // Prepare multipart form payload using browser's FormData
      const formData = new FormData();
      for (let i = 0; i < imageFiles.length; i++) {
          // 'auto' lets PlantNet guess the organ type
          formData.append('organs', 'auto');
          formData.append('images', imageFiles[i], imageFiles[i].name); // Append File object
      }

      // API request execution using axios
      try {
        const response = await axios.post(
          `${PLANTNET_API_URL}?api-key=${apiKey}`,
          formData,
          {
            headers: {
              // Axios sets Content-Type to multipart/form-data automatically for FormData
              // 'Content-Type': 'multipart/form-data', // Usually not needed with axios and FormData
            }
          }
        );
        // Return the full response data structure from PlantNet
        return response.data; // Axios provides data directly in response.data
      } catch (error) {
        let message = 'PlantNet API request failed.';
        if (error.response) {
          // The request was made and the server responded with a status code
          // that falls out of the range of 2xx
          console.error('PlantNet API Error Response:', error.response.data);
          message = error.response.data?.message || `HTTP Error ${error.response.status}`;
        } else if (error.request) {
          // The request was made but no response was received
          console.error('PlantNet API No Response:', error.request);
          message = 'No response received from PlantNet API. Check network connection.';
        } else {
          // Something happened in setting up the request that triggered an Error
          console.error('PlantNet API Request Setup Error:', error.message);
          message = `Error setting up request: ${error.message}`;
        }
        throw new Error(message);
      }
    }

    // ======================
    // DATA PROCESSING & OUTPUT (Helper function, can be used in frontend)
    // ======================

    /**
     * Processes raw API response into a potentially simplified/structured format if needed.
     * This example focuses on adding a timestamp and extracting key fields.
     * @param {Object} apiData - Raw response data from PlantNet API identifyPlant function
     * @returns {Object} Processed data structure (similar to species.json)
     */
    function processResults(apiData) {
        if (!apiData || !apiData.results) {
            console.warn("Received incomplete data from PlantNet API:", apiData);
            // Return a structure indicating failure or partial data
             return {
                 timestamp: new Date().toISOString(),
                 error: "Incomplete data received from API.",
                 bestMatch: null,
                 results: [],
                 remainingRequests: apiData?.remainingIdentificationRequests || 'Unknown'
             };
        }

      // Extract top result(s) - example: top 1 result
      const topResults = apiData.results.slice(0, 1).map(result => ({
        score: Number(result.score.toFixed(5)), // Control precision
        taxonomy: {
          scientificName: result.species?.scientificNameWithoutAuthor || 'N/A',
          genus: result.species?.genus?.scientificNameWithoutAuthor || 'N/A',
          family: result.species?.family?.scientificNameWithoutAuthor || 'N/A'
        },
        commonNames: result.species?.commonNames || [],
        conservation: {
          // Safely access IUCN data
          status: result.iucn?.category || 'Not assessed',
          source: result.iucn ? 'IUCN Red List' : null
        },
        references: {
          // Safely access reference IDs
          gbif: result.gbif?.id || null,
          powo: result.powo?.id || null
        }
        // You could add result.images here if you need PlantNet's example images
      }));


      return {
        // Metadata
        timestamp: new Date().toISOString(), // ISO 8601 format
        apiVersion: apiData.version || 'Unknown', // Include API version if available

        // Identification results
        bestMatch: apiData.bestMatch || (topResults.length > 0 ? topResults[0].taxonomy.scientificName : 'N/A'),
        results: topResults, // Include the processed top result(s)

        // API status
        remainingRequests: apiData.remainingIdentificationRequests !== undefined ? apiData.remainingIdentificationRequests : 'Unreported'
      };
    }

    // ======================
    // EXECUTION HANDLER (Reference Script Usage)
    // ======================
    // This part runs only when the script is executed directly using Node.js
    // In the webapp, the frontend component triggers the identification flow.
    if (require.main === module) {
      const imagePaths = process.argv.slice(2); // Get image paths from command line args

      if (imagePaths.length === 0) {
          console.error("Usage: node plantnet.js <image_path_1> [image_path_2] ...");
          process.exit(1);
      }

      // Convert paths to File-like objects for identifyPlant (simulation)
      // In a real frontend, you get File objects from the input element directly.
      const fileObjects = imagePaths.map(imgPath => {
          try {
              // Basic simulation: read file content for FormData usage
              return fs.createReadStream(imgPath);
              // Note: For the real identifyPlant expecting File objects, this adaptation is needed
              // if you wanted to run this script *exactly* like the frontend would call it.
              // However, the reference script uses fs.createReadStream directly with form-data library.
          } catch (e) {
               console.error(`Error accessing file: ${imgPath}`, e.message);
               return null;
          }
      }).filter(Boolean);


      if (fileObjects.length === 0) {
           console.error("No valid image files could be accessed.");
           process.exit(1);
      }


      (async () => {
        try {
          // Execute identification request (using fs streams as per original script intent)
          console.log(`Identifying plant from: ${imagePaths.join(', ')}...`);

          // Re-implementing the direct call with fs streams for standalone script execution
          const form = new FormData();
          imagePaths.forEach((imagePath) => {
             try {
                  form.append('organs', 'auto');
                  form.append('images', fs.createReadStream(imagePath));
             } catch (e) {
                  console.warn(`Could not read file ${imagePath}, skipping. Error: ${e.message}`);
             }
          });

          const response = await axios.post(
            `${PLANTNET_API_URL}?api-key=${API_KEY}`,
            form,
            { headers: form.getHeaders() } // form-data library specific headers
          );
          const rawApiData = response.data; // Actual API data


          // Process and save results (Reference output)
          const processedData = processResults(rawApiData);
          fs.writeFileSync('species.json', JSON.stringify(processedData, null, 2));

          console.log("\n--- Identification Results ---");
          console.log(`Timestamp: ${processedData.timestamp}`);
          console.log(`Best Match: ${processedData.bestMatch}`);
          if (processedData.results.length > 0) {
               const topResult = processedData.results[0];
               console.log(`  Score: ${topResult.score}`);
               console.log(`  Common Names: ${topResult.commonNames.join(', ') || 'None'}`);
               console.log(`  Conservation: ${topResult.conservation.status}`);
          }
          console.log(`API Requests Remaining: ${processedData.remainingRequests}`);
          console.log(`\n✅ Reference results saved to species.json`);


        } catch (error) {
          console.error(`\n--- Execution Failed ---`);
          console.error(error.message);
          // Log additional details if available
          if (error.response?.data) {
               console.error("API Error Details:", error.response.data);
          }
          process.exit(1);
        }
      })();
    }

    // Export functions if this were a module (useful for testing)
    // module.exports = { identifyPlant, processResults };
    ```

---

## 5. `guardian.py`

*   **Purpose:** This file serves as **documentation and defines the expected JSON data structure** for alerts and data readings sent *from* a Guardian sensor device (Raspberry Pi) *to* the Foresta backend. It is **not** a script that the web application itself runs.
*   **Integration Point:** **Backend**. The backend API endpoint `/api/sensors/data` (defined in `/app/api/sensors.py` or similar) needs to be designed to receive, validate, and parse JSON payloads matching this structure. The logic in the backend service (`/app/services/sensor_service.py`) will handle storing this data appropriately in the `Sensors`, `Alerts`, and `SensorReadings` database tables.
*   **Input:** N/A (Defines a format).
*   **Output:** N/A (Defines a format).

*   **Example Data Format (`sensor.json` - represents payload sent *to* the backend):**

    ```json
    {
      "alert_id": "a3f4b91c-7d2e-4b5a-934f-5e9b8a2c1d0f", // Unique ID generated by sensor or backend upon receive
      "code_name": "Guardian-Michuki-Memorial-Park-12", // Unique identifier of the sending Pi sensor
      "timestamp": "2024-03-21T14:35:22Z", // ISO 8601 timestamp of the reading/event

      "gps_coordinates": { // Required for locating the sensor/event
        "latitude": -1.292066,
        "longitude": 36.821528
      },

      "battery_info": { // Optional but useful for maintenance
        "percentage": 82.3,
        "voltage": 5.2
      },

      "environment": { // Standard environmental readings
        "temperature": 38.4, // Celsius
        "humidity": 28.5 // Percentage (Optional)
      },

      "detections": { // Presence indicates a potential alert event
        "fire": { // Fire detection data
          "confidence": 0.0, // AI/Rule based confidence (0-1)
          "sensor_data": {
            "temp": 41.2, // Specific sensor reading relevant to fire
            "smoke_level": 0.05 // Smoke sensor reading (0-1 or ppm)
          }
        },
        "logging": { // Illegal logging detection data
          "confidence": 0.87, // AI audio model confidence (0-1)
          "audio_type": "chainsaw" // Classified sound type ("chainsaw", "vehicle", "unknown")
        }
      },

      "system_health": { // Optional: Pi system status
        "uptime": 43200, // Seconds since last reboot
        "storage_free": 1024.8 // Available storage in MB
      }
    }
    ```

*   **Script Code (Documentation Only):**

    ```python
    """
    Guardian Sensor Data Format Specification (sensor.json)

    Purpose:
    This document defines the standard JSON structure for data and alerts transmitted
    from Guardian field sensor units (Raspberry Pi based) to the Foresta backend API endpoint.
    It is NOT an executable script run by the web application, but rather a specification
    for the data payload format.

    Integration Point:
    - Backend: The API endpoint `/api/sensors/data` must expect POST requests with a JSON body
      adhering to this format. Validation and parsing logic in the backend service layer
      (`/app/services/sensor_service.py`) will process this data.
    - Sensor Simulator: The `sensor_simulator.py` script will generate JSON data matching this
      format to send to the backend for testing.
    - Physical Guardian Device: The software running on the actual Raspberry Pi sensor units
      must construct and send JSON payloads in this format.

    Key Fields:
    - alert_id: Unique identifier for the specific message/alert (can be UUID).
    - code_name: Pre-configured unique identifier for the physical sensor device.
    - timestamp: ISO 8601 formatted time of the event or reading.
    - gps_coordinates: Essential for locating the sensor. Latitude/Longitude in WGS84 decimal degrees.
    - battery_info: Optional health metric for the sensor device.
    - environment: Standard sensor readings (temperature, humidity).
    - detections: Contains confidence scores and specific data related to detected events (fire, logging).
                  The presence and confidence values within this object often trigger alert creation in the backend.
    - system_health: Optional diagnostic information about the sensor device itself.

    Backend Processing Notes:
    1. Validation: Backend must validate incoming JSON against this schema (check for required fields, data types, ranges).
    2. Authentication/Authorization: How does the backend verify the request comes from a legitimate sensor? (e.g., Pre-shared keys, device certificates, API tokens associated with `code_name`). This needs implementation.
    3. Data Storage:
       - Update `Sensors` table: `last_seen`, `status`, `battery_percentage`, potentially `latitude`, `longitude` if they can change.
       - Store readings: `temperature`, `humidity` might go into `SensorReadings` table (if historical trends are needed) or just update the latest state in `Sensors`.
       - Create `Alerts`: If `detections.fire.confidence` or `detections.logging.confidence` exceed defined thresholds, create a new record in the `Alerts` table, storing relevant parts of the `detections` block in `details_json`.
    4. Real-time Forwarding: If an alert is generated, the backend might push a notification via WebSockets to connected frontend clients viewing the relevant area.

    Example Payload (see JSON block below this documentation in the original file):
    Represents a typical message, in this case indicating a high confidence detection of logging activity.
    """

    # This file is documentation. No executable Python code is needed here to define the format.
    # The JSON example provided separately serves as the concrete specification.

    pass # Placeholder to make it a valid Python file if needed for tooling.
    ```

---

## 6. `sensor_simulator.py` (Placeholder)

*   **Purpose:** Mimics the behavior of a real Guardian sensor device by sending simulated data (in the format defined by `sensor.json`) to the backend's sensor data endpoint. This is essential for development and testing of the backend API, database storage, and frontend monitoring pages without requiring physical hardware.
*   **Integration Point:** **Standalone Script**. Run from the command line in a separate terminal. It acts as an external client sending data *to* the backend.
*   **Input:**
    *   Command-line arguments:
        *   `--endpoint`: URL of the backend sensor endpoint (e.g., `http://localhost:5000/api/sensors/data`).
        *   `--sensor-id`: The `code_name` to use for the simulated sensor (e.g., `SIMULATOR-01`).
        *   `--lat`, `--lon`: GPS coordinates for the simulated sensor.
        *   `--interval`: Time in seconds between sending regular data readings (e.g., `60`).
        *   Optional flags to trigger specific alerts (e.g., `--send-fire-alert`, `--send-logging-alert`).
*   **Output:**
    *   Sends HTTP POST requests containing JSON payloads (matching `sensor.json` format) to the specified backend endpoint.
    *   Prints status messages to the console (e.g., "Sending reading...", "Sent fire alert.", "Error sending data: ...").

*   **Example Input (Command Line):**
    ```bash
    python sensor_simulator.py --endpoint http://localhost:5000/api/sensors/data --sensor-id SIMULATOR-01 --lat -1.2833 --lon 36.8167 --interval 30
    ```
    ```bash
    python sensor_simulator.py --endpoint http://localhost:5000/api/sensors/data --sensor-id SIMULATOR-01 --lat -1.2833 --lon 36.8167 --send-fire-alert
    ```

*   **Example Output (JSON Payload Sent to Backend - matches `sensor.json` format):**
    *(The simulator would randomly generate or increment values within realistic ranges for fields like temperature, humidity, battery, confidence scores etc., based on whether it's sending a normal reading or a specific alert.)*

*   **Script Code (Placeholder - Needs Implementation):**

    ```python
    #!/usr/bin/env python3
    """
    Foresta Guardian Sensor Simulator

    Purpose:
    Simulates a Guardian sensor device by sending periodic data readings and
    triggered alerts to the specified backend API endpoint. Uses the data format
    defined in the 'sensor.json' specification.

    Usage:
    python sensor_simulator.py --endpoint <backend_url> --sensor-id <id> --lat <latitude> --lon <longitude> [--interval <seconds>] [--send-fire-alert] [--send-logging-alert]

    Example:
    # Send regular readings every 60 seconds
    python sensor_simulator.py --endpoint http://localhost:5000/api/sensors/data --sensor-id SIM-GUARD-01 --lat -1.292 --lon 36.821 --interval 60

    # Send a single high-confidence fire alert immediately
    python sensor_simulator.py --endpoint http://localhost:5000/api/sensors/data --sensor-id SIM-GUARD-01 --lat -1.292 --lon 36.821 --send-fire-alert

    Dependencies:
    - requests
    """

    import requests
    import json
    import time
    import random
    import uuid
    from datetime import datetime, timezone
    import argparse

    def generate_reading(sensor_id: str, lat: float, lon: float) -> Dict:
        """Generates a standard sensor reading with realistic random values."""
        ts = datetime.now(timezone.utc).isoformat(timespec='seconds') + 'Z'
        return {
          "alert_id": str(uuid.uuid4()),
          "code_name": sensor_id,
          "timestamp": ts,
          "gps_coordinates": {
            "latitude": lat,
            "longitude": lon
          },
          "battery_info": {
            "percentage": round(random.uniform(60.0, 99.0), 1),
            "voltage": round(random.uniform(4.8, 5.3), 1)
          },
          "environment": {
            "temperature": round(random.uniform(15.0, 35.0), 1), # Normal temp range
            "humidity": round(random.uniform(30.0, 80.0), 1)
          },
          "detections": { # Low confidence for standard reading
            "fire": {
              "confidence": round(random.uniform(0.0, 0.15), 2),
              "sensor_data": {
                "temp": round(random.uniform(16.0, 38.0), 1),
                "smoke_level": round(random.uniform(0.01, 0.1), 2)
              }
            },
            "logging": {
              "confidence": round(random.uniform(0.0, 0.2), 2),
              "audio_type": random.choice(["unknown", "vehicle", "wind"]) # Less likely chainsaw
            }
          },
          "system_health": {
            "uptime": random.randint(3600, 86400 * 7), # 1hr to 1 week
            "storage_free": round(random.uniform(500.0, 2000.0), 1)
          }
        }

    def generate_fire_alert(sensor_id: str, lat: float, lon: float) -> Dict:
        """Generates a high-confidence fire alert."""
        reading = generate_reading(sensor_id, lat, lon) # Start with a base reading
        reading["alert_id"] = str(uuid.uuid4()) # New ID for the alert
        reading["timestamp"] = datetime.now(timezone.utc).isoformat(timespec='seconds') + 'Z'
        # Modify for fire conditions
        reading["environment"]["temperature"] = round(random.uniform(45.0, 80.0), 1) # Higher temp
        reading["detections"]["fire"]["confidence"] = round(random.uniform(0.85, 0.99), 2) # High confidence
        reading["detections"]["fire"]["sensor_data"]["temp"] = reading["environment"]["temperature"] + random.uniform(5, 20) # Sensor temp even higher
        reading["detections"]["fire"]["sensor_data"]["smoke_level"] = round(random.uniform(0.7, 0.95), 2) # High smoke
        # Optional: Lower logging confidence during fire
        reading["detections"]["logging"]["confidence"] = round(random.uniform(0.0, 0.1), 2)
        print(f"*** Generated Fire Alert for {sensor_id} ***")
        return reading

    def generate_logging_alert(sensor_id: str, lat: float, lon: float) -> Dict:
        """Generates a high-confidence logging alert."""
        reading = generate_reading(sensor_id, lat, lon) # Start with a base reading
        reading["alert_id"] = str(uuid.uuid4()) # New ID for the alert
        reading["timestamp"] = datetime.now(timezone.utc).isoformat(timespec='seconds') + 'Z'
        # Modify for logging conditions
        reading["detections"]["logging"]["confidence"] = round(random.uniform(0.8, 0.98), 2) # High confidence
        reading["detections"]["logging"]["audio_type"] = "chainsaw" # Specific sound
        # Optional: Normal fire confidence during logging
        reading["detections"]["fire"]["confidence"] = round(random.uniform(0.0, 0.1), 2)
        print(f"*** Generated Logging Alert for {sensor_id} ***")
        return reading

    def send_data(endpoint: str, data: Dict):
        """Sends the data payload to the backend endpoint."""
        headers = {'Content-Type': 'application/json'}
        try:
            response = requests.post(endpoint, headers=headers, data=json.dumps(data), timeout=10)
            response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)
            print(f"[{datetime.now()}] Sent data for {data['code_name']} (Alert ID: {data['alert_id']}). Status: {response.status_code}")
            return True
        except requests.exceptions.RequestException as e:
            print(f"[{datetime.now()}] Error sending data for {data['code_name']}: {e}")
            return False
        except Exception as e:
             print(f"[{datetime.now()}] An unexpected error occurred during send: {e}")
             return False

    def main():
        parser = argparse.ArgumentParser(description="Simulate a Foresta Guardian Sensor.")
        parser.add_argument("--endpoint", required=True, help="Backend API endpoint URL (e.g., http://localhost:5000/api/sensors/data)")
        parser.add_argument("--sensor-id", required=True, help="Unique identifier for the simulated sensor (code_name)")
        parser.add_argument("--lat", type=float, required=True, help="Latitude coordinate")
        parser.add_argument("--lon", type=float, required=True, help="Longitude coordinate")
        parser.add_argument("--interval", type=int, default=0, help="Interval in seconds for sending regular readings. If 0 or omitted, sends one reading and exits (unless an alert flag is set).")
        parser.add_argument("--send-fire-alert", action="store_true", help="Send a single high-confidence fire alert and exit.")
        parser.add_argument("--send-logging-alert", action="store_true", help="Send a single high-confidence logging alert and exit.")

        args = parser.parse_args()

        if args.send_fire_alert:
            payload = generate_fire_alert(args.sensor_id, args.lat, args.lon)
            send_data(args.endpoint, payload)
        elif args.send_logging_alert:
            payload = generate_logging_alert(args.sensor_id, args.lat, args.lon)
            send_data(args.endpoint, payload)
        elif args.interval > 0:
            print(f"Starting simulation for sensor {args.sensor_id}. Sending readings every {args.interval} seconds. Press Ctrl+C to stop.")
            while True:
                payload = generate_reading(args.sensor_id, args.lat, args.lon)
                send_data(args.endpoint, payload)
                try:
                    time.sleep(args.interval)
                except KeyboardInterrupt:
                    print("\nSimulation stopped by user.")
                    break
        else:
            # Send one standard reading and exit
            print(f"Sending a single reading for sensor {args.sensor_id} and exiting.")
            payload = generate_reading(args.sensor_id, args.lat, args.lon)
            send_data(args.endpoint, payload)

    if __name__ == "__main__":
        main()

    ```

---
