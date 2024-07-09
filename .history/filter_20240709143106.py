import json
import matplotlib.pyplot as plt
import re
from datetime import datetime
import pandas as pd

# Load the data from the JSON file
with open('products.json', 'r', encoding='utf-8') as f:
    products = json.load(f)

# Function to filter out non-laptop products
def is_laptop(product):
    if "Notebook" in product['name'] or "laptop" in product['name']:
        return True
    return False

# Filter the list of products to include only laptops
laptops = [product for product in products if is_laptop(product)]

# Function to extract price from price string
def extract_price(price_str):
    prices = re.findall(r'\d+', price_str.replace(' ', ''))
    if prices:
        return int(prices[0])
    return None

# Current date
current_date = datetime.now().strftime('%Y-%m-%d')

# Extract prices and use the current date
price_data = []

for laptop in laptops:
    price = extract_price(laptop['price'])
    if price is not None:
        price_data.append({'date': current_date, 'price': price})

# Convert to DataFrame
df = pd.DataFrame(price_data)

# Calculate statistics
price_stats = df.groupby('date')['price'].agg(['min', 'max', 'mean']).reset_index()

# Plot the data
plt.figure(figsize=(12, 6))
plt.plot(price_stats['date'], price_stats['min'], label='Minimum Price', color='blue')
plt.plot(price_stats['date'], price_stats['max'], label='Maximum Price', color='red')
plt.plot(price_stats['date'], price_stats['mean'], label='Average Price', color='orange')
plt.fill_between(price_stats['date'], price_stats['min'], price_stats['max'], color='grey', alpha=0.2)
plt.title('Price Range for Laptops')
plt.xlabel('Date')
plt.ylabel('Price (Ft)')
plt.legend()
plt.grid(True)
plt.show()
