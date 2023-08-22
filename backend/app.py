from flask import Flask, render_template, request, redirect, url_for
import requests
from pathlib import Path
import json
import random

# ARDUINO_URL = "http://192.168.16.156"
ARDUINO_URL = "http://10.32.36.33"
db_file = (Path(__file__).parent/"db.json")

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

@app.route("/verification/<int:total>/<user_id>/<order_id>")
def verification(total, user_id, order_id):
    data = get_db()
    data["current_student_id"] = user_id
    # new_order_id = str(int(data["last_order_id"]) + 1).zfill(4)
    # print(data)
    user_name = data["users"][user_id]["name"]
    order_data = { "name" : user_name, "order_id" : order_id, "order_total": total}

    # NOTE: You could save the order ID and it's details in the database
    data["last_order_id"] = order_id
    data["last_order_total"] = total
    write_db(data)
    return render_template("verification.html", order_data=order_data)

@app.route("/complete_transaction")
def complete_transaction():
    data = get_db()
    order_details = {"order_id": data["last_order_id"],
                     "order_total" : data["last_order_total"],
                     "student" : data["users"][data["current_student_id"]]["name"]
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
    if (current_student in data["users"]) :
        if current_student==finger_id :
            #check balance
            balance = data["users"][finger_id]["balance"]
            print(balance)
            if (balance >= order_total):
                new_balance = balance - order_total
                result = True
            else:
                error = "Balance too low"
        else:
            error = "False identity"
    else:
        error = "Invalid user ID"
    return {"valid" : result, "error": error}

if __name__ == "__main__":
    app.run(debug=True)
