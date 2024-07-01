import mysql.connector

config = {
    'user': 'seoreoco_alex',
    'password': 'Lietadlo123321',
    'host': 'euukult1.armadaservers.com',  # or the server's public IP
    'database': 'seoreoco_ranked',
    'raise_on_warnings': True
}

try:
    conn = mysql.connector.connect(**config)
    if conn.is_connected():
        print("Connected successfully to the database")

    # Your code to interact with the database goes here

finally:
    if conn.is_connected():
        conn.close()
        print("Connection closed")
