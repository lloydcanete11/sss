"""
ShuttlePro — Flask Backend
Stack: Python + Flask + SQLite
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3, os, json, hashlib, datetime

app = Flask(__name__, static_folder="static")
CORS(app)

DB = "shuttlepro.db"

# ─────────────────────────────────────────
#  Database bootstrap
# ─────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS products (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            name     TEXT NOT NULL,
            brand    TEXT NOT NULL,
            category TEXT NOT NULL,
            price    REAL NOT NULL,
            old_price REAL,
            badge    TEXT,
            icon     TEXT,
            description TEXT,
            stock    INTEGER DEFAULT 50,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS users (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            name     TEXT NOT NULL,
            email    TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS orders (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT NOT NULL,
            items    TEXT NOT NULL,
            total    REAL NOT NULL,
            status   TEXT DEFAULT 'pending',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS cart (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            product_id INTEGER NOT NULL,
            qty      INTEGER DEFAULT 1,
            FOREIGN KEY(product_id) REFERENCES products(id)
        );
        """)

        # Seed products if empty
        row = db.execute("SELECT COUNT(*) as c FROM products").fetchone()
        if row["c"] == 0:
            products = [
                ("Astrox 99 Pro",      "Yonex",   "racket",  8990, 10990, "new",  "🏸", "Head-heavy attacking racket with rotational generator system.", 30),
                ("Windstorm 72",        "Victor",  "racket",  5490, 6990,  "sale", "🏸", "Extra-slim frame for lightning-fast swing speed.", 25),
                ("Aeronaut 9000",       "Li-Ning", "racket",  7200, None,  None,   "🏸", "Carbon-fiber frame designed for all-court dominance.", 20),
                ("N90-III",             "Yonex",   "racket",  4200, None,  None,   "🏸", "Iconic offensive racket trusted by champions worldwide.", 15),
                ("AS-9 Feather",        "RSL",     "shuttle", 650,  None,  "new",  "🪶", "Grade-A goose feather shuttlecock for tournament play.", 100),
                ("Mavis 350",           "Yonex",   "shuttle", 380,  None,  None,   "🪶", "Durable nylon shuttlecock for practice and training.", 80),
                ("Power Feather Pro",   "Carlton", "shuttle", 720,  820,   "sale", "🪶", "Elite feather shuttle approved for international matches.", 60),
                ("SHB 65Z III",         "Yonex",   "shoes",   6800, None,  "new",  "👟", "Ultra-lightweight court shoe with Power Cushion technology.", 40),
                ("Great One",           "Victor",  "shoes",   5200, 6200,  "sale", "👟", "Excellent grip and shock absorption for quick lateral cuts.", 35),
                ("Ranger 2.0",          "Apacs",   "shoes",   3900, None,  None,   "👟", "Affordable high-performance court shoe for everyday play.", 50),
                ("Pro Racket Bag 9R",   "Yonex",   "bag",     3200, None,  None,   "🎒", "Holds 9 rackets with thermal lining and multi-pocket storage.", 20),
                ("Team Backpack",       "Victor",  "bag",     1850, 2200,  "sale", "🎒", "Spacious backpack with shoe compartment and hydration slot.", 30),
                ("BG80 Power",          "Yonex",   "string",  320,  None,  None,   "🎵", "High-tension string for powerful smashing.", 200),
                ("VBS-66N Nano",        "Victor",  "string",  280,  None,  "new",  "🎵", "Control-focused string for precise placement shots.", 150),
            ]
            db.executemany("""INSERT INTO products
                (name,brand,category,price,old_price,badge,icon,description,stock)
                VALUES (?,?,?,?,?,?,?,?,?)""", products)
            db.commit()

# ─────────────────────────────────────────
#  Static frontend
# ─────────────────────────────────────────
@app.route("/")
def index():
    return send_from_directory("static", "index.html")

# ─────────────────────────────────────────
#  Products API
# ─────────────────────────────────────────
@app.route("/api/products", methods=["GET"])
def get_products():
    cat = request.args.get("category", "all")
    with get_db() as db:
        if cat == "all":
            rows = db.execute("SELECT * FROM products ORDER BY id").fetchall()
        else:
            rows = db.execute("SELECT * FROM products WHERE category=? ORDER BY id", (cat,)).fetchall()
    return jsonify([dict(r) for r in rows])

@app.route("/api/products/<int:pid>", methods=["GET"])
def get_product(pid):
    with get_db() as db:
        row = db.execute("SELECT * FROM products WHERE id=?", (pid,)).fetchone()
    if not row:
        return jsonify({"error": "Not found"}), 404
    return jsonify(dict(row))

@app.route("/api/products/search", methods=["GET"])
def search_products():
    q = request.args.get("q", "")
    with get_db() as db:
        rows = db.execute(
            "SELECT * FROM products WHERE name LIKE ? OR brand LIKE ? OR description LIKE ?",
            (f"%{q}%", f"%{q}%", f"%{q}%")
        ).fetchall()
    return jsonify([dict(r) for r in rows])

# ─────────────────────────────────────────
#  Cart API (session-based)
# ─────────────────────────────────────────
@app.route("/api/cart/<session_id>", methods=["GET"])
def get_cart(session_id):
    with get_db() as db:
        rows = db.execute("""
            SELECT c.id, c.qty, p.name, p.price, p.icon, p.brand, p.badge
            FROM cart c JOIN products p ON c.product_id = p.id
            WHERE c.session_id = ?
        """, (session_id,)).fetchall()
    items = [dict(r) for r in rows]
    total = sum(i["price"] * i["qty"] for i in items)
    return jsonify({"items": items, "total": total, "count": sum(i["qty"] for i in items)})

@app.route("/api/cart/<session_id>/add", methods=["POST"])
def add_to_cart(session_id):
    data = request.get_json()
    pid  = data.get("product_id")
    qty  = data.get("qty", 1)
    with get_db() as db:
        existing = db.execute(
            "SELECT id, qty FROM cart WHERE session_id=? AND product_id=?",
            (session_id, pid)
        ).fetchone()
        if existing:
            db.execute("UPDATE cart SET qty=? WHERE id=?", (existing["qty"] + qty, existing["id"]))
        else:
            db.execute("INSERT INTO cart (session_id, product_id, qty) VALUES (?,?,?)", (session_id, pid, qty))
        db.commit()
    return jsonify({"success": True, "message": "Added to cart"})

@app.route("/api/cart/<session_id>/remove/<int:cart_id>", methods=["DELETE"])
def remove_from_cart(session_id, cart_id):
    with get_db() as db:
        db.execute("DELETE FROM cart WHERE id=? AND session_id=?", (cart_id, session_id))
        db.commit()
    return jsonify({"success": True})

@app.route("/api/cart/<session_id>/clear", methods=["DELETE"])
def clear_cart(session_id):
    with get_db() as db:
        db.execute("DELETE FROM cart WHERE session_id=?", (session_id,))
        db.commit()
    return jsonify({"success": True})

# ─────────────────────────────────────────
#  Auth API
# ─────────────────────────────────────────
def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

@app.route("/api/auth/register", methods=["POST"])
def register():
    d = request.get_json()
    try:
        with get_db() as db:
            db.execute(
                "INSERT INTO users (name, email, password) VALUES (?,?,?)",
                (d["name"], d["email"], hash_pw(d["password"]))
            )
            db.commit()
        return jsonify({"success": True, "message": "Account created!"})
    except sqlite3.IntegrityError:
        return jsonify({"success": False, "message": "Email already registered"}), 409

@app.route("/api/auth/login", methods=["POST"])
def login():
    d = request.get_json()
    with get_db() as db:
        user = db.execute(
            "SELECT * FROM users WHERE email=? AND password=?",
            (d["email"], hash_pw(d["password"]))
        ).fetchone()
    if user:
        return jsonify({"success": True, "user": {"name": user["name"], "email": user["email"]}})
    return jsonify({"success": False, "message": "Invalid credentials"}), 401

# ─────────────────────────────────────────
#  Orders API
# ─────────────────────────────────────────
@app.route("/api/orders", methods=["POST"])
def place_order():
    d = request.get_json()
    session_id = d.get("session_id")
    user_email = d.get("email", "guest@shuttlepro.ph")

    with get_db() as db:
        rows = db.execute("""
            SELECT c.qty, p.name, p.price, p.icon
            FROM cart c JOIN products p ON c.product_id = p.id
            WHERE c.session_id = ?
        """, (session_id,)).fetchall()

        if not rows:
            return jsonify({"success": False, "message": "Cart is empty"}), 400

        items = [dict(r) for r in rows]
        total = sum(i["price"] * i["qty"] for i in items)

        db.execute(
            "INSERT INTO orders (user_email, items, total) VALUES (?,?,?)",
            (user_email, json.dumps(items), total)
        )
        db.execute("DELETE FROM cart WHERE session_id=?", (session_id,))
        db.commit()

    return jsonify({"success": True, "message": "Order placed!", "total": total})

@app.route("/api/orders/<email>", methods=["GET"])
def get_orders(email):
    with get_db() as db:
        rows = db.execute(
            "SELECT * FROM orders WHERE user_email=? ORDER BY created_at DESC",
            (email,)
        ).fetchall()
    orders = []
    for r in rows:
        o = dict(r)
        o["items"] = json.loads(o["items"])
        orders.append(o)
    return jsonify(orders)

# ─────────────────────────────────────────
#  Stats API (admin-ish)
# ─────────────────────────────────────────
@app.route("/api/stats", methods=["GET"])
def get_stats():
    with get_db() as db:
        total_products = db.execute("SELECT COUNT(*) as c FROM products").fetchone()["c"]
        total_orders   = db.execute("SELECT COUNT(*) as c FROM orders").fetchone()["c"]
        total_users    = db.execute("SELECT COUNT(*) as c FROM users").fetchone()["c"]
        revenue        = db.execute("SELECT COALESCE(SUM(total),0) as s FROM orders WHERE status='pending'").fetchone()["s"]
    return jsonify({
        "products": total_products,
        "orders":   total_orders,
        "users":    total_users,
        "revenue":  revenue
    })

# ─────────────────────────────────────────
#  Newsletter
# ─────────────────────────────────────────
@app.route("/api/newsletter", methods=["POST"])
def newsletter():
    email = request.get_json().get("email", "")
    if "@" not in email:
        return jsonify({"success": False, "message": "Invalid email"}), 400
    return jsonify({"success": True, "message": "Subscribed! 15% off code: SMASH15"})

# ─────────────────────────────────────────
if __name__ == "__main__":
    os.makedirs("static", exist_ok=True)
    init_db()
    print("✅  ShuttlePro backend running at http://localhost:5000")
    app.run(debug=True, port=5000)
