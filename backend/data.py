import mysql.connector
import json
import os

# Get the absolute path to the JSON file
script_dir = os.path.dirname(__file__)
file_path = os.path.join(script_dir, 'db.json')

# Read the JSON configuration file
with open(file_path, 'r') as db_file:
    config = json.load(db_file)
# Establish a MySQL database connection
try:
    conn = mysql.connector.connect(
        host=config["host"],
        user=config["user"],
        password=config["password"],
        database=config["database"]
    )

    if conn.is_connected():
        print("Connected to MySQL database")

    # Now, you can execute SQL queries to fetch data from the database
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM trans")
    data = cursor.fetchall()

    for row in data:
        print(row)

except mysql.connector.Error as err:
    print(f"Error: {err}")

finally:
    if conn.is_connected():
        cursor.close()
        conn.close()
        print("MySQL connection is closed")
