from flask import Flask, send_file
app = Flask(__name__)

@app.route("/data.json")
def data():
    r = send_file("/home/USUARIO/data.json", mimetype="application/json")
    r.headers["Access-Control-Allow-Origin"] = "*"
    r.headers["Cache-Control"] = "no-cache"
    return r
