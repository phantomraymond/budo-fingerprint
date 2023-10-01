from flask import Flask, render_template, request, redirect, url_for
import requests
from pathlib import Path
import json
import mysql.connector
import uuid

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

    # Fetch student data and create a dictionary
    cursor.execute("SELECT student_id, student_name FROM student")
    users = {}
    for student_id, student_name in cursor.fetchall():
        users[student_id] = {
            "name": student_name,
            "total_deposit": 0,  # Initialize total_deposit to 0 for each user
            "total_order": 0,    # Initialize total_order to 0 for each user
            "balance": 0      # Initialize difference to 0 for each user
        }

    # Fetch deposit data and calculate total_deposit per user
    cursor.execute("SELECT student_id, SUM(amount) FROM deposit GROUP BY student_id")
    for student_id, total_deposit in cursor.fetchall():
        if student_id in users:
            users[student_id]["total_deposit"] = total_deposit

    # Fetch order data and calculate total_order per user
    cursor.execute("SELECT student_id, SUM(order_total) FROM `order` GROUP BY student_id")
    for student_id, total_order in cursor.fetchall():
        if student_id in users:
            users[student_id]["total_order"] = total_order

    # Calculate the difference for each user
    for student_id, data in users.items():
        data["balance"] = data["total_deposit"] - data["total_order"]

    # Create a dictionary to hold the results
    result = {
        "users": users
    }

    # Write the results to a JSON file named db.json
    with open("db.json", "w") as json_file:
        json.dump(result, json_file, indent=4)

except mysql.connector.Error as err:
    print(f"Error: {err}")

finally:
    if conn.is_connected():
        conn.close()
        print("MySQL connection is closed")

# ARDUINO_URL = "http://192.168.16.156"
ARDUINO_URL = "http://localhost:8000"
db_file = (Path(__file__).parent / "db.json")

app = Flask(__name__)

# Rest of the code remains the same...


# Rest of the code remains the same...


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

@app.route("/verification/<int:total>/<student_id>/<order_id>")
def verification(total, student_id, order_id):
    data = get_db()

    # Check if the student_id is valid
    if student_id in data["users"]:
        user_name = data["users"][student_id]["name"]
        
        # Save the order ID and its details in the database
        try:
            conn = mysql.connector.connect(**config)
            cursor = conn.cursor()

            insert_query = "INSERT INTO `order` (student_id, order_id, order_total) VALUES (%s, %s, %s)"
            cursor.execute(insert_query, (student_id, order_id, total))
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

        order_data = {"name": user_name, "order_id": order_id, "order_total": total}
        return render_template("verification.html", order_data=order_data)
    else:
        error_message = "Invalid student ID"
        return render_template("verification.html", error=error_message)

# ... (remaining code)
# ... (previous code)

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
    
    # ask Arduino for id
    res = requests.get(ARDUINO_URL)
    print(res)
    finger_id = res.json()["id"]
    result = False
    error = ""
    
    if current_student in data["student"]:
        if current_student == finger_id:
            # check balance
            balance = data["student"][finger_id]["balance"]
            print(balance)
            if balance >= order_total:
                new_balance = balance - order_total
                result = True
            else:
                error = "Balance too low"
        else:
            error = "False identity"
    else:
        error = "Invalid student ID"
    
    return {"valid": result, "error": error}

if __name__ == "__main__":
    app.run(debug=True)
