from flask import Flask, render_template

from routers.auth import auth
from routers.group import group


app = Flask(__name__)


# =========================
# REGISTER BLUEPRINTS
# =========================

app.register_blueprint(auth)
app.register_blueprint(group)


# =========================
# HOME PAGE
# =========================

@app.route("/")
def home():
    return render_template("index.html")


# =========================
# DASHBOARD
# =========================

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


# =========================
# GROUP PAGE
# =========================

@app.route("/group/<int:group_id>")
def group_page(group_id):
    return render_template("group.html")

# =========================
# SETTLEMENT PAGE
# =========================

@app.route("/settlement/<int:group_id>")
def settlement_page(group_id):
    return render_template("settlement.html")


# =========================
# RUN SERVER
# =========================

if __name__ == "__main__":
   app.run(host="0.0.0.0", port=5000, debug=True)