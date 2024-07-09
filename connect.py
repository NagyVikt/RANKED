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

# Drop tables if they exist
drop_products_table_query = "DROP TABLE IF EXISTS Products"
drop_categories_table_query = "DROP TABLE IF EXISTS Categories"
execute_query(connection, drop_products_table_query)
execute_query(connection, drop_categories_table_query)

# Create Categories table query
create_categories_table_query = """
CREATE TABLE IF NOT EXISTS Categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE
);
"""

# Create Products table query with foreign key reference to Categories
create_products_table_query = """
CREATE TABLE IF NOT EXISTS Products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    link VARCHAR(255) NOT NULL,
    image_url VARCHAR(255),
    description TEXT,
    RAM VARCHAR(50),
    GPU VARCHAR(50),
    SSD VARCHAR(50),
    weight DECIMAL(5, 2),
    rating DECIMAL(3, 2),
    price DECIMAL(10, 2),
    original_price DECIMAL(10, 2),
    stock_status INT,
    order_code VARCHAR(50),
    category_id INT,
    FOREIGN KEY (category_id) REFERENCES Categories(id)
);
"""

# Execute create table queries
execute_query(connection, create_categories_table_query)
execute_query(connection, create_products_table_query)

# Read JSON data from file
with open('alza_products.json', 'r', encoding='utf-8') as file:
    data = json.load(file)

# Insert data into the Categories table and get the category ID
def get_category_id(connection, category_name):
    select_category_query = "SELECT id FROM Categories WHERE name = %s"
    insert_category_query = "INSERT INTO Categories (name) VALUES (%s)"
    cursor = connection.cursor()
    cursor.execute(select_category_query, (category_name,))
    category = cursor.fetchone()
    if category:
        return category[0]
    else:
        cursor.execute(insert_category_query, (category_name,))
        connection.commit()
        return cursor.lastrowid

# Process only the first three JSON objects
products = data[:3]

# Insert data into the Products table
insert_product_query = """
INSERT INTO Products (name, link, image_url, description, RAM, GPU, SSD, weight, rating, price, original_price, stock_status, order_code, category_id)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
"""

for product in products:
    name = product['name']
    link = product['link']
    image_url = product.get('image_url', None)
    description = product.get('description', None)
    RAM = product.get('RAM', None)
    GPU = product.get('GPU', None)
    SSD = product.get('SSD', None)
    weight = float(product.get('weight', 0).replace(',', '.')) if product.get('weight') else None
    rating = product['rating']
    if isinstance(rating, str):
        rating = float(rating.replace(',', '.'))  # Replace comma with period if rating is a string
    price = float(product['price'])
    original_price = float(product.get('original_price', 0))
    stock_status = int(product['stock_status'])
    order_code = product['order_code']
    category_name = product['category']
    category_id = get_category_id(connection, category_name)

    product_data = (name, link, image_url, description, RAM, GPU, SSD, weight, rating, price, original_price, stock_status, order_code, category_id)
    execute_query(connection, insert_product_query, product_data)

# Close the connection
if connection:
    connection.close()
    print("MySQL connection is closed")
