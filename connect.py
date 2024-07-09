import mysql.connector
from mysql.connector import Error
import json

def create_connection(config):
    connection = None
    try:
        connection = mysql.connector.connect(**config)
        print("Connection to MySQL DB successful")
    except Error as e:
        print(f"The error '{e}' occurred")
    return connection

def execute_query(connection, query, data=None):
    cursor = connection.cursor()
    try:
        if data:
            cursor.execute(query, data)
        else:
            cursor.execute(query)
        connection.commit()
        print("Query executed successfully")
    except Error as e:
        print(f"The error '{e}' occurred")

def execute_read_query(connection, query):
    cursor = connection.cursor()
    result = None
    try:
        cursor.execute(query)
        result = cursor.fetchall()
        return result
    except Error as e:
        print(f"The error '{e}' occurred")

# Connection configuration
config = {
    'user': 'seoreoco_itrexalex',
    'password': 'Lietadlo123321',
    'host': '139.162.199.190',  # or the server's public IP
    'database': 'seoreoco_itrex',
    'raise_on_warnings': True
}

# Establishing the connection
connection = create_connection(config)

# Drop table if it exists
drop_table_query = "DROP TABLE IF EXISTS Products"
execute_query(connection, drop_table_query)

# Create table query
create_table_query = """
CREATE TABLE IF NOT EXISTS Products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    link VARCHAR(255) NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    rating DECIMAL(3, 2) NOT NULL,
    reviews_count INT NOT NULL
);
"""

# Execute create table query
execute_query(connection, create_table_query)

# Read JSON data from file
with open('alza_products.json', 'r', encoding='utf-8') as file:
    data = json.load(file)

# Process only the first three JSON objects
products = data[:3]

# Insert data into the table
insert_product_query = """
INSERT INTO Products (name, link, price, rating, reviews_count)
VALUES (%s, %s, %s, %s, %s)
"""

for product in products:
    name = product['name']
    link = product['link']
    price = float(product['price'].replace('€', '').replace('\xa0', '').replace(' ', '').strip())
    rating = float(product['rating'].replace(',', '.'))  # Replace comma with period
    reviews_count = int(product['reviews_count'].replace('×', '').strip())

    product_data = (name, link, price, rating, reviews_count)
    execute_query(connection, insert_product_query, product_data)

# Close the connection
if connection:
    connection.close()
    print("MySQL connection is closed")
