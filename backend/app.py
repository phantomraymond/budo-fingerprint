from flask import Flask, render_template, request, redirect, url_for
import requests
from pathlib import Path
import json
import random
import mysql.connector
import uuid  # Import UUID for generating unique order IDs

# Database connection configuration
config = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "bio"
}

try:
    # Establish a MySQL database connection
    conn = mysql.connector.connect(**config)

    if conn.is_connected():
        print("Connected to MySQL database")

    # Create a cursor to execute SQL queries
    cursor = conn.cursor()

    # Execute your SQL query to fetch data (replace with your actual query)
    cursor.execute("SELECT * FROM trans")
    data = cursor.fetchall()

    # Define a dictionary to store user data
    users = {}

    # Iterate through the fetched data and create user objects
    for row in data:
        user_id = row[0]
        user_data = {
            "name": row[1],
            "balance": row[2]
        }
        users[user_id] = user_data

    # Create a dictionary to store the "users" key with the user data
    output_data = {"users": users}

    # Define the output JSON file path
    json_file_path = "db.json"

    # Write the data to a JSON file
    with open(json_file_path, "w") as json_file:
        json.dump(output_data, json_file, indent=4)

    print(f"Data saved to {json_file_path}")

except mysql.connector.Error as err:
    print(f"Error: {err}")

finally:
    if conn.is_connected():
        cursor.close()
        conn.close()
        print("MySQL connection is closed")

# ARDUINO_URL = "http://192.168.16.156"
ARDUINO_URL = "http://localhost:8000"
db_file = (Path(__file__).parent / "db.json")
# db_file = (Path(__file__).parent/"data.py")

app = Flask(__name__)

def get_db():
    data = db_file.read_text()
    f = json.loads(data)
    return f

def write_db(new_data):
    data = json.dumps(new_data)
    db_file.write_text(data)
    return True

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/order")
def order():
    return render_template("order.html")

@app.route("/checkout")
def checkout():
    return render_template("checkout.html")

@app.route("/payment")
def payment():
    return render_template("payment.html")

@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/db")
def db():
    return get_db()

@app.route("/verification/<int:total>/<user_id>")
def verification(total, user_id):
    data = get_db()

    # Generate a unique order ID using UUID
    order_id = str(uuid.uuid4())

    data["current_student_id"] = user_id
    user_name = data["users"][user_id]["name"]
    order_data = {"name": user_name, "order_id": order_id, "order_total": total}

    # Save the order ID and its details in the database
    try:
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()

        insert_query = "INSERT INTO orders (user_id, order_id, order_total) VALUES (%s, %s, %s)"
        cursor.execute(insert_query, (user_id, order_id, total))
        conn.commit()

    except mysql.connector.Error as err:
        print(f"Database Error: {err}")

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

    # Update the database with the last order ID and order total
    data["last_order_id"] = order_id
    data["last_order_total"] = total
    write_db(data)

    return render_template("verification.html", order_data=order_data)

@app.route("/complete_transaction")
def complete_transaction():
    data = get_db()
    order_details = {"order_id": data["last_order_id"],
                     "order_total": data["last_order_total"],
                     "student": data["users"][data["current_student_id"]]["name"]
                     }

    return render_template("complete_transaction.html", order_details=order_details)

@app.route("/arduino/<int:order_total>")
def arduino(order_total):
    data = get_db()
    current_student = data["current_student_id"]
    print("hello")
    print(data)
    # ask arduino for id
    res = requests.get(ARDUINO_URL)
    print(res)
    finger_id = res.json()["id"]
    result = False
    error = ""
    if current_student in data["users"]:
        if current_student == finger_id:
            # check balance
            balance = data["users"][finger_id]["balance"]
            print(balance)
            if balance >= order_total:
                new_balance = balance - order_total
                result = True
            else:
                error = "Balance too low"
        else:
            error = "False identity"
    else:
        error = "Invalid user ID"
    return {"valid": result, "error": error}

if __name__ == "__main__":
    app.run(debug=True)
