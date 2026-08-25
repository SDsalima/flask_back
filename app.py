from flask import Flask, jsonify, request, redirect
import sqlite3
import os
import hashlib

app = Flask(__name__)


def get_db_conn():
    dir_base = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(dir_base, "product.db")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


@app.route("/init", methods=["GET"])
def init_db():
    conn = get_db_conn()
    conn.execute("""
            CREATE TABLE IF NOT EXISTs products(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL
            )
""")
    conn.execute("""
            CREATE TABLE IF NOT EXISTs users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
            )
""")

    count = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
    if count == 0:
        conn.executemany(
            "INSERT INTO products (name, price) VALUES (?, ?)",
            [
                ("Widget", 9.99),
                ("Gadget", 19.99),
                ("Gizmo", 14.50),
            ],
        )

    conn.commit()
    conn.close()
    return jsonify({"message": "Database init complete!"})


@app.route("/")
def home():
    return jsonify({"message": "This is our first server"})


@app.route("/products", methods=["GET"])
def get_products():
    conn = get_db_conn()
    rows = conn.execute("SELECT * FROM products").fetchall()
    conn.close()
    return jsonify([dict(row) for row in rows])


@app.route("/products", methods=["POST"])
def add_products():
    data = request.get_json()
    name = data.get("name")
    price = data.get("price")

    conn = get_db_conn()
    cursor = conn.execute(
        "INSERT INTO products (name,price) VALUES (?,?)",
        (
            name,
            price,
        ),
    )
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()

    new_product = {"id": new_id, "name": name, "price": price}
    return jsonify({"message": f"product added!\n{new_product}"}), 201


@app.route("/products/<int:product_id>", methods=["PUT"])
def update_product(product_id):
    data = request.get_json()
    name = data.get("name")
    price = data.get("price")

    conn = get_db_conn()
    conn.execute(
        "UPDATE products SET name=?,price=? WHERE id=?",
        (
            name,
            price,
            product_id,
        ),
    )
    conn.commit()
    conn.close()
    return jsonify({"message": f"Product {product_id} updated!"}), 201


@app.route("/products/<int:product_id>", methods=["DELETE"])
def delete_product(product_id):
    conn = get_db_conn()
    conn.execute("DELETE FROM products WHERE id=?", (product_id,))
    conn.commit()
    conn.close()
    return jsonify({"message": f"Product {product_id} has been deleted!"}), 201


@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "missing username or password!"}), 400

    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    try:
        conn = get_db_conn()
        conn.execute(
            "INSERT INTO users (username,password) VALUES (?,?)",
            (username, hashed_password),
        )
        conn.commit()
        conn.close()
        return jsonify({"message": "User register successfully"}), 201

    except sqlite3.IntegrityError:
        return jsonify({"message": f"{username} already exist!."}), 409


@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    if not username and not password:
        return jsonify({"Error": "Missing username or password!"}), 401
    hashed_password = hashlib.sha3_256(password.encode()).hexdigest()
    conn = get_db_conn()
    user = conn.execute(
        "SELECT * FROM users WHERE username = ? AND password = ?",
        (username, hashed_password),
    ).fetchone()
    if user:
        return jsonify({"message": f"Welcome {username}!"}), 201
    else:
        return jsonify({"error": "Invalid credential"}), 401


if __name__ == "__main__":
    with app.app_context():
        init_db()
    app.run(debug=True)
