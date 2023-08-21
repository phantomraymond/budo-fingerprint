from pathlib import Path
from time import sleep

from flask import Flask

app = Flask(__name__)

@app.route("/")
def index():
    if Path("identity_status").read_text() == "T":
        sleep(7)
        return {"id" : "3"}
    else:
        sleep(9)
        return {"id" : "10"}


if __name__ == "__main__":
    app.run("0.0.0.0", 8000, debug=True)
