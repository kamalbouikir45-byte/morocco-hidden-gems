"""
Maroc Authentique — Flask + MySQL backend
==========================================

Endpoints:
  GET  /                     -> serves the static site (index.html)
  GET  /api/villages         -> list all villages (optional ?type=&search=)
  GET  /api/villages/<id>    -> single village
  POST /api/reservations     -> create a reservation
  GET  /api/reservations     -> list reservations (simple admin view)

Run:
  pip install -r requirements.txt
  python app.py          # then open http://localhost:5000
"""

import os
import sqlite3
from flask import Flask, jsonify, request, send_from_directory, session
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__, static_folder="static")

app.secret_key = os.getenv("SECRET_KEY", "change-me-in-production")

CORS(app, supports_credentials=True)

DATABASE = "database.db"


# ===========================
# Database
# ===========================

def get_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # ---------------- Users ----------------
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL
    )
    """)

    # ---------------- Villages ----------------
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS villages(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        region TEXT NOT NULL,
        type TEXT NOT NULL,
        description TEXT NOT NULL,
        price REAL NOT NULL,
        image TEXT NOT NULL
    )
    """)

    # ---------------- Reservations ----------------
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reservations(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT NOT NULL,
        visit_date TEXT NOT NULL,
        place TEXT NOT NULL,
        visitor_type TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()

    # Insert demo villages only once
    cursor.execute("SELECT COUNT(*) FROM villages")
    total = cursor.fetchone()[0]

    if total == 0:

        villages = [

            (
                "Chefchaouen",
                "Tanger-Tétouan",
                "Culturel",
                "La célèbre ville bleue du Maroc.",
                250,
                "static/images/chefchaouen.jpg"
            ),

            (
                "Merzouga",
                "Drâa-Tafilalet",
                "Désert",
                "Découvrez les dunes de l'Erg Chebbi.",
                400,
                "static/images/merzouga.jpg"
            ),

            (
                "Imlil",
                "Marrakech-Safi",
                "Montagne",
                "Village situé au pied du Toubkal.",
                180,
                "static/images/imlil.jpg"
            ),

            (
                "Ouzoud",
                "Béni Mellal-Khénifra",
                "Naturel",
                "Magnifiques cascades naturelles.",
                220,
                "static/images/ouzoud.jpg"
            )

        ]

        cursor.executemany("""
        INSERT INTO villages
        (name, region, type, description, price, image)
        VALUES (?, ?, ?, ?, ?, ?)
        """, villages)

        conn.commit()

    conn.close()


init_db()


# ---------------------------------------------------------------------------
# Static site
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    return send_from_directory(".", "index.html")


@app.route("/login")
def login_page():
    return send_from_directory(".", "login.html")


@app.route("/admin")
def admin_page():
    return send_from_directory(".", "admin.html")


@app.route("/<path:path>")
def static_proxy(path):
    """Serve other static files (css/js/images) by their relative path."""
    return send_from_directory(".", path)


# =====================================================
# Authentication
# =====================================================

@app.route("/api/register", methods=["POST"])
def register():

    data = request.get_json() or {}

    name = data.get("name", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not name or not email or not password:
        return jsonify({"error": "Tous les champs sont obligatoires."}), 400

    if len(password) < 6:
        return jsonify({"error": "Le mot de passe doit contenir au moins 6 caractères."}), 400

    password_hash = generate_password_hash(password)

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id FROM users WHERE email = ?",
        (email,)
    )

    if cursor.fetchone():

        conn.close()

        return jsonify({
            "error": "Cet email existe déjà."
        }), 409

    cursor.execute("""
        INSERT INTO users
        (name,email,password_hash)
        VALUES (?,?,?)
    """, (
        name,
        email,
        password_hash
    ))

    conn.commit()

    user_id = cursor.lastrowid

    conn.close()

    session["user_id"] = user_id
    session["user_name"] = name

    return jsonify({

        "message": "Compte créé avec succès.",

        "user": {

            "id": user_id,
            "name": name,
            "email": email

        }

    }), 201


# =====================================================

@app.route("/api/login", methods=["POST"])
def login():

    data = request.get_json() or {}

    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({
            "error": "Email et mot de passe requis."
        }), 400

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""

        SELECT
            id,
            name,
            email,
            password_hash

        FROM users

        WHERE email=?

    """, (email,))

    user = cursor.fetchone()

    conn.close()

    if user is None:

        return jsonify({
            "error": "Email ou mot de passe incorrect."
        }), 401

    if not check_password_hash(user["password_hash"], password):

        return jsonify({
            "error": "Email ou mot de passe incorrect."
        }), 401

    session["user_id"] = user["id"]
    session["user_name"] = user["name"]

    return jsonify({

        "message": "Connexion réussie.",

        "user": {

            "id": user["id"],
            "name": user["name"],
            "email": user["email"]

        }

    })


# =====================================================

@app.route("/api/logout", methods=["POST"])
def logout():

    session.clear()

    return jsonify({
        "message": "Déconnexion réussie."
    })


# =====================================================

@app.route("/api/me")
def me():

    if "user_id" not in session:

        return jsonify({
            "error": "Non authentifié."
        }), 401

    return jsonify({

        "id": session["user_id"],
        "name": session["user_name"]

    })
# =====================================================
# Villages
# =====================================================

VALID_TYPES = (
    "Montagne",
    "Désert",
    "Culturel",
    "Naturel"
)


@app.route("/api/villages", methods=["GET"])
def list_villages():

    search = request.args.get("search", "").strip()
    vtype = request.args.get("type", "").strip()

    conn = get_connection()
    cursor = conn.cursor()

    query = """
        SELECT
            id,
            name,
            region,
            type,
            description,
            price,
            image
        FROM villages
        WHERE 1=1
    """

    params = []

    if vtype:

        query += " AND type=?"

        params.append(vtype)

    if search:

        query += """
            AND
            (
                name LIKE ?
                OR region LIKE ?
                OR description LIKE ?
            )
        """

        like = f"%{search}%"

        params.extend([like, like, like])

    query += " ORDER BY name ASC"

    cursor.execute(query, params)

    villages = []

    for row in cursor.fetchall():

        villages.append({

            "id": row["id"],
            "name": row["name"],
            "region": row["region"],
            "type": row["type"],
            "description": row["description"],
            "price": row["price"],
            "image": row["image"]

        })

    conn.close()

    return jsonify(villages)


# =====================================================

@app.route("/api/villages/<int:village_id>", methods=["GET"])
def get_village(village_id):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""

        SELECT
            id,
            name,
            region,
            type,
            description,
            price,
            image

        FROM villages

        WHERE id=?

    """, (village_id,))

    row = cursor.fetchone()

    conn.close()

    if row is None:

        return jsonify({

            "error": "Village introuvable."

        }), 404

    return jsonify({

        "id": row["id"],
        "name": row["name"],
        "region": row["region"],
        "type": row["type"],
        "description": row["description"],
        "price": row["price"],
        "image": row["image"]

    })


# =====================================================

@app.route("/api/villages", methods=["POST"])
def create_village():

    data = request.get_json() or {}

    name = data.get("name", "").strip()
    region = data.get("region", "").strip()
    vtype = data.get("type", "").strip()
    description = data.get("description", "").strip()

    image = data.get(
        "image",
        "static/images/hero.png"
    ).strip()

    try:

        price = float(data.get("price", 0))

    except:

        return jsonify({

            "error": "Prix invalide."

        }), 400

    if not all([name, region, vtype, description]):

        return jsonify({

            "error": "Tous les champs sont obligatoires."

        }), 400

    if vtype not in VALID_TYPES:

        return jsonify({

            "error": "Type invalide."

        }), 400

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""

        INSERT INTO villages

        (
            name,
            region,
            type,
            description,
            price,
            image
        )

        VALUES
        (
            ?,?,?,?,?,?
        )

    """, (

        name,
        region,
        vtype,
        description,
        price,
        image

    ))

    conn.commit()

    village_id = cursor.lastrowid

    conn.close()

    return jsonify({

        "message": "Village ajouté.",

        "id": village_id

    }), 201


# =====================================================

@app.route("/api/villages/<int:village_id>", methods=["PUT"])
def update_village(village_id):

    data = request.get_json() or {}

    name = data.get("name", "").strip()
    region = data.get("region", "").strip()
    vtype = data.get("type", "").strip()
    description = data.get("description", "").strip()

    image = data.get("image", "").strip()

    try:

        price = float(data.get("price", 0))

    except:

        return jsonify({

            "error": "Prix invalide."

        }), 400

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""

        UPDATE villages

        SET

            name=?,
            region=?,
            type=?,
            description=?,
            price=?,
            image=?

        WHERE id=?

    """, (

        name,
        region,
        vtype,
        description,
        price,
        image,
        village_id

    ))

    conn.commit()

    conn.close()

    return jsonify({

        "message": "Village mis à jour."

    })


# =====================================================

@app.route("/api/villages/<int:village_id>", methods=["DELETE"])
def delete_village(village_id):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute(

        "DELETE FROM villages WHERE id=?",

        (village_id,)

    )

    conn.commit()

    conn.close()

    return jsonify({

        "message": "Village supprimé."

    })
# =====================================================
# Admin Statistics
# =====================================================

@app.route("/api/stats", methods=["GET"])
def stats():

    conn = get_connection()
    cursor = conn.cursor()

    # --------------------------
    # Total villages
    # --------------------------

    cursor.execute("SELECT COUNT(*) FROM villages")
    total_villages = cursor.fetchone()[0]

    # --------------------------
    # Total reservations
    # --------------------------

    cursor.execute("SELECT COUNT(*) FROM reservations")
    total_reservations = cursor.fetchone()[0]

    # --------------------------
    # Villages by type
    # --------------------------

    cursor.execute("""

        SELECT
            type,
            COUNT(*) AS total

        FROM villages

        GROUP BY type

    """)

    by_type = {}

    for row in cursor.fetchall():

        by_type[row["type"]] = row["total"]

    # --------------------------
    # Reservations per month
    # --------------------------

    cursor.execute("""

        SELECT

            strftime('%m', visit_date) AS month,

            COUNT(*) AS total

        FROM reservations

        GROUP BY month

        ORDER BY month

    """)

    monthly = [0] * 12

    for row in cursor.fetchall():

        if row["month"]:

            index = int(row["month"]) - 1

            monthly[index] = row["total"]

    conn.close()

    return jsonify({

        "total_villages": total_villages,

        "total_reservations": total_reservations,

        "by_type": by_type,

        "monthly": monthly

    })
# =====================================================
# Reservations
# =====================================================

@app.route("/api/reservations", methods=["POST"])
def create_reservation():

    data = request.get_json() or {}

    name = data.get("name", "").strip()
    email = data.get("email", "").strip().lower()
    date = data.get("date", "").strip()
    place = data.get("place", "").strip()
    visitor_type = data.get("visitor_type", "National").strip()

    if not all([name, email, date, place]):
        return jsonify({
            "error": "Tous les champs sont obligatoires."
        }), 400

    if visitor_type not in ("National", "Étranger"):
        return jsonify({
            "error": "Type de visiteur invalide."
        }), 400

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""

        INSERT INTO reservations
        (
            name,
            email,
            visit_date,
            place,
            visitor_type
        )

        VALUES
        (
            ?,?,?,?,?
        )

    """, (

        name,
        email,
        date,
        place,
        visitor_type

    ))

    conn.commit()

    reservation_id = cursor.lastrowid

    conn.close()

    return jsonify({

        "message": "Réservation enregistrée.",

        "id": reservation_id

    }), 201


# =====================================================

@app.route("/api/reservations", methods=["GET"])
def list_reservations():

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""

        SELECT

            id,
            name,
            email,
            visit_date,
            place,
            visitor_type,
            created_at

        FROM reservations

        ORDER BY created_at DESC

    """)

    reservations = []

    for row in cursor.fetchall():

        reservations.append({

            "id": row["id"],
            "name": row["name"],
            "email": row["email"],
            "visit_date": row["visit_date"],
            "place": row["place"],
            "visitor_type": row["visitor_type"],
            "created_at": row["created_at"]

        })

    conn.close()

    return jsonify(reservations)


# =====================================================

@app.route("/api/reservations/<int:reservation_id>", methods=["DELETE"])
def delete_reservation(reservation_id):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute(

        "DELETE FROM reservations WHERE id=?",

        (reservation_id,)

    )

    conn.commit()

    deleted = cursor.rowcount

    conn.close()

    if deleted == 0:

        return jsonify({

            "error": "Réservation introuvable."

        }), 404

    return jsonify({

        "message": "Réservation supprimée."

    })


# =====================================================
# Health Check (for Render)
# =====================================================

@app.route("/health")
def health():

    return jsonify({

        "status": "ok",

        "database": "sqlite"

    })


# =====================================================

if __name__ == "__main__":

    app.run(

        host="0.0.0.0",

        port=int(os.environ.get("PORT", 5000)),

        debug=True

    )

