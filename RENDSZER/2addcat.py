import json
from settings import INPUT_JSON_FILE, OUTPUT_JSON_FILE, TARGETID

# Load the category configuration
categories = [
    {"id": 81, "name": "ALVE létrák", "slug": "alve-letrak"},
    {"id": 72, "name": "Brennenstuhl hosszabbító kábelek és lámpatestek", "slug": "brennenstuhl-hosszabbitokabelek-es-lampatestek"},
    {"id": 78, "name": "Csapágyak, tömítések, ékszíjak és tartozékok", "slug": "csapagyak-tomitesek-ekszijak-es-tartozekok"},
    {"id": 71, "name": "Egyéni védőeszközök Delta plus", "slug": "egyeni-vedoeszkozok-delta-plus"},
    {"id": 69, "name": "Emelő- és kezelőtechnika YALE-PFAFF", "slug": "emelo-es-kezelo-technika-yale-pfaff"},
    {"id": 66, "name": "Emelőtechnika, kampók és láncok 80-as és 100-as osztály", "slug": "emelo-technika-kampok-es-lancok-80-as-es-100-as-osztaly"},
    {"id": 75, "name": "Építőkémia", "slug": "epitokemia"},
    {"id": 68, "name": "Feszítőpántok – gurtnik és tartozékok", "slug": "feszitopantok-gurtnik-es-tartozekok"},
    {"id": 77, "name": "Háztartás és drogéria", "slug": "haztartas-es-drogeria"},
    {"id": 65, "name": "Kötelek, láncok és gyorskötözők", "slug": "kotelek-lancok-es-gyorskotozok"},
    {"id": 64, "name": "Kötéltartozékok és rozsdamentes acél program", "slug": "koteltartozekok-es-rozsdamentes-acel-program"},
    {"id": 74, "name": "Kötő- és rögzítőelemek", "slug": "koto-es-rogzitoelemek"},
    {"id": 67, "name": "Lánc- és textilhevederek", "slug": "lanc-es-textilhevederek"},
    {"id": 82, "name": "Mágnesek", "slug": "magnesek"},
    {"id": 70, "name": "Sarkak, szögvasak és vasalatok", "slug": "sarkak-szogvasak-es-vasalatok"},
    {"id": 76, "name": "Szerszámok", "slug": "szerszamok"},
    {"id": 79, "name": "Szövetek", "slug": "szovetek"},
    {"id": 15, "name": "Uncategorized", "slug": "uncategorized"},
    {"id": 73, "name": "Villanyszerelési anyagok", "slug": "villanyszerelesi-anyagok"}
]

# Create a dictionary for quick category lookup by name
category_dict = {category["id"]: category for category in categories}

# Load JSON data from a file
with open(INPUT_JSON_FILE, 'r', encoding='utf-8') as file:
    products = json.load(file)

# Define the target category ID for all products
target_category_id = TARGETID

# Update categories field for each product
for product in products:
    category = category_dict.get(target_category_id)
    if category:
        product["categories"] = [category]

# Save the updated JSON data back to the file
with open(OUTPUT_JSON_FILE, 'w', encoding='utf-8') as file:
    json.dump(products, file, indent=4, ensure_ascii=False)

print("The file has been updated with categories.")
