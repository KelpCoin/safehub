import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__, instance_relative_config=True)

# Config (safe defaults; override via .env if you like)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-change-me")
os.makedirs(app.instance_path, exist_ok=True)
db_path = os.path.join(app.instance_path, "safehub.sqlite")
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", f"sqlite:///{db_path}")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"

# ----- Models -----
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ----- Routes -----
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/products")
def products():
    items = [
        {"name": "Murmur Weighted Tee", "price": "NZ", "tag": "flagship", "desc": "Weighted, sensory-soft tee for calming pressure."},
        {"name": "NeuroGlow Tee",       "price": "NZ",  "tag": "sensory",  "desc": "Ultra-soft, tagless, flat seams."},
        {"name": "BodyHarmony Tee",     "price": "NZ",  "tag": "unisex+",  "desc": "Extended sizing, drape fit, body-positive."},
    ]
    return render_template("products.html", items=items)

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name","").strip()
        email = request.form.get("email","").lower().strip()
        password = request.form.get("password","")
        if not name or not email or not password:
            flash("All fields are required.", "warning"); return redirect(url_for("register"))
        if User.query.filter_by(email=email).first():
            flash("Email already registered.", "warning"); return redirect(url_for("register"))
        u = User(name=name, email=email, password_hash=generate_password_hash(password))
        db.session.add(u); db.session.commit()
        login_user(u); flash(f"Welcome to SafeHub, {u.name}!", "success")
        return redirect(url_for("products"))
    return render_template("register.html")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email","").lower().strip()
        password = request.form.get("password","")
        u = User.query.filter_by(email=email).first()
        if u and check_password_hash(u.password_hash, password):
            login_user(u); flash("Signed in.", "success"); return redirect(url_for("products"))
        flash("Invalid credentials.", "danger"); return redirect(url_for("login"))
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user(); flash("Signed out.", "info")
    return redirect(url_for("index"))

def init_db():
    with app.app_context():
        db.create_all()

if __name__ == "__main__":
    init_db()
    app.run(host="127.0.0.1", port=5000, debug=True)
