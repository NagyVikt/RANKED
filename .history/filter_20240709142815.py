import json
import matplotlib.pyplot as plt
import re
import pandas as pd
from datetime import datetime, timedelta

# Load the data from the JSON file
with open('/mnt/data/products.json', 'r', encoding='utf-8') as f:
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

# Generate a simulated date range for demonstration purposes
def generate_date_range(num_entries, start_date='2023-01-01'):
    base_date = datetime.strptime(start_date, '%Y-%m-%d')
    return [base_date + timedelta(days=i) for i in range(num_entries)]

# Extract prices and simulate dates
dates = generate_date_range(len(laptops))
price_data = []

for laptop, date in zip(laptops, dates):
    price = extract_price(laptop['price'])
    if price is not None:
        price_data.append({'date': date, 'price': price})

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
plt.title('Price Range for Laptops Over Time')
plt.xlabel('Date')
plt.ylabel('Price (Ft)')
plt.legend()
plt.grid(True)
plt.show()
