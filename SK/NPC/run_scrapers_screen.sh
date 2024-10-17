#!/bin/bash

# Ensure the script exits if any command fails
set -e

# Array of category slugs
slugs=(

  "naradie-zahradne-naradie"
  "naradie-znackovace-a-ceruzky"
  "nezaradene"
  "ochranne-pracovne-prostriedky-delta-plus"
  "ochranne-pracovne-prostriedky-delta-plus-ciapky-kukly-siltovky-rukavice"
  "ochranne-pracovne-prostriedky-delta-plus-dazd"
  "CUCC-dealt-kotviace-zariadenia-systemy-na-udrziavanie-pracovnej-polohy"
  "ochranne-pracovne-prostriedky-delta-plus-ochrana-dychacich-ciest"
  "ochranne-pracovne-prostriedky-delta-plus-ochrana-hlavy"
  "ochranne-pracovne-prostriedky-delta-plus-ochrana-lebky"
  "ochranne-pracovne-prostriedky-delta-plus-ochrana-pri-praci-vo-vyskach"
  "ochranne-pracovne-prostriedky-delta-plus-ochrana-ruk"
  "ochranne-pracovne-prostriedky-delta-plus-ochrana-sluchu"
  "ochranne-pracovne-prostriedky-delta-plus-ochrana-tela"
  "ochranne-pracovne-prostriedky-delta-plus-ochrana-zraku"
  "ochranne-pracovne-prostriedky-delta-plus-pracovna-obuv-indoor"
  "ochranne-pracovne-prostriedky-delta-plus-pracovna-obuv-outdoor"
)
# Path to the Python script
SCRIPT_PATH="product_scraper.py"

# Path to the categories JSON
CATEGORIES_JSON="filtered_categories.json"

# Loop through each slug and create a screen session
for slug in "${slugs[@]}"; do
  # Define the output JSON filename
  output_json="${slug}.json"

  # Define a unique screen session name (replace hyphens with underscores for compatibility)
  session_name="scraper_${slug//-/_}"

  # Check if a screen session with this name already exists
  if screen -list | grep -q "$session_name"; then
    echo "Screen session '$session_name' already exists. Skipping..."
    continue
  fi

  echo "Creating screen session '$session_name' and starting scraper..."

  # Create a detached screen session and run the scraper command
  screen -dmS "$session_name" bash -c "python \"$SCRIPT_PATH\" --category_slug \"$slug\" --categories \"$CATEGORIES_JSON\" --output \"$output_json\""

  # Optional: Brief pause to prevent overwhelming the system
  sleep 0.1
done

echo "All screen sessions have been initiated."
