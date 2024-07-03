import mysql.connector
from mysql.connector import Error

def create_connection(config):
    connection = None
    try:
        connection = mysql.connector.connect(**config)
        print("Connection to MySQL DB successful")
    except Error as e:
        print(f"The error '{e}' occurred")
    return connection

def execute_query(connection, query):
    cursor = connection.cursor()
    try:
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
    'user': 'seoreoco_alex',
    'password': 'Lietadlo123321',
    'host': '139.162.199.190',  # or the server's public IP
    'database': 'seoreoco_ranked',
    'raise_on_warnings': True
}

# Establishing the connection
connection = create_connection(config)

# Example query to fetch all data from DomainCim
select_domains = "SELECT * FROM DomainCim"
domains = execute_read_query(connection, select_domains)

for domain in domains:
    print(domain)

# Example query to fetch domains with their plans
select_domains_with_plans = """
SELECT DomainCim.domain_name, Plan.name AS plan_name
FROM DomainCim
INNER JOIN Plan ON DomainCim.plan_id = Plan.id;
"""
domains_with_plans = execute_read_query(connection, select_domains_with_plans)

for domain_with_plan in domains_with_plans:
    print(domain_with_plan)
