from flask import Flask, render_template, url_for
import json
import os
from datetime import datetime

app = Flask(__name__)

# Function to load JSON data from a file
def load_json_data(json_file):
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data

# Function to load all JSON files from the MINTAK directory
def load_all_categories(directory):
    categories = {}
    for filename in os.listdir(directory):
        if filename.endswith('.json'):
            category_name = filename.replace('.json', '').replace('-', ' ').title()
            filepath = os.path.join(directory, filename)
            products = load_json_data(filepath)
            # Get the last modified time of the file
            last_modified_time = os.path.getmtime(filepath)
            last_modified_date = datetime.fromtimestamp(last_modified_time).strftime('%B %d, %Y %H:%M:%S')
            categories[category_name] = {
                'products': products,
                'count': len(products),
                'last_updated': last_modified_date
            }
    return categories

# Home route to display all categories
@app.route('/')
def home():
    categories = load_all_categories('MINTAK')
    return render_template('categories.html', categories=categories)

# Route to display products in a category
@app.route('/category/<category_name>')
def category(category_name):
    categories = load_all_categories('MINTAK')
    selected_category = categories.get(category_name.replace('-', ' ').title(), None)
    if selected_category:
        return render_template('table.html', category_name=category_name, products=selected_category['products'])
    else:
        return "Category not found", 404

if __name__ == '__main__':
    app.run(debug=True)
