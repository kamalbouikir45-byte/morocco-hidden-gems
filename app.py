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
from flask import Flask, jsonify, request, send_from_directory, session
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector
from mysql.connector import Error

app = Flask(__name__, static_folder="static")
# Secret key signs the session cookie — override in production.
app.secret_key = os.getenv("SECRET_KEY", "change-me-in-production")
CORS(app, supports_credentials=True)  # allow the frontend to send the session cookie

# ---------------------------------------------------------------------------
# Database configuration (override with environment variables in production)
# ---------------------------------------------------------------------------
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "maroc_authentique"),
    "port": int(os.getenv("DB_PORT", "3306")),
}


def get_connection():
    """Open a new MySQL connection."""
    return mysql.connector.connect(**DB_CONFIG)


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


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------
@app.route("/api/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    # Server-side validation
    if not all([name, email, password]):
        return jsonify({"error": "Tous les champs sont obligatoires."}), 400
    if "@" not in email or "." not in email:
        return jsonify({"error": "Adresse email invalide."}), 400
    if len(password) < 6:
        return jsonify({"error": "Le mot de passe doit contenir au moins 6 caractères."}), 400

    password_hash = generate_password_hash(password)

    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        # Reject duplicate emails
        cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({"error": "Un compte existe déjà avec cet email."}), 409

        cursor.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (%s, %s, %s)",
            (name, email, password_hash),
        )
        conn.commit()
        user_id = cursor.lastrowid
        cursor.close()
        conn.close()

        # Log the new user in immediately
        session["user_id"] = user_id
        session["user_name"] = name
        return jsonify({"message": "Compte créé", "user": {"id": user_id, "name": name, "email": email}}), 201
    except Error as e:
        return jsonify({"error": f"Database error: {e}"}), 500


@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not all([email, password]):
        return jsonify({"error": "Email et mot de passe requis."}), 400

    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, name, email, password_hash FROM users WHERE email = %s",
            (email,),
        )
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user is None or not check_password_hash(user["password_hash"], password):
            return jsonify({"error": "Email ou mot de passe incorrect."}), 401

        session["user_id"] = user["id"]
        session["user_name"] = user["name"]
        return jsonify(
            {"message": "Connecté", "user": {"id": user["id"], "name": user["name"], "email": user["email"]}}
        )
    except Error as e:
        return jsonify({"error": f"Database error: {e}"}), 500


@app.route("/api/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"message": "Déconnecté"})


@app.route("/api/me", methods=["GET"])
def me():
    """Return the currently logged-in user (or 401 if not authenticated)."""
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Non authentifié"}), 401
    return jsonify({"id": user_id, "name": session.get("user_name")})


# ---------------------------------------------------------------------------
# Villages
# ---------------------------------------------------------------------------
@app.route("/api/villages", methods=["GET"])
def list_villages():
    search = request.args.get("search", "").strip()
    vtype = request.args.get("type", "").strip()

    query = "SELECT id, name, region, type, description, price, image FROM villages WHERE 1=1"
    params = []

    if vtype:
        query += " AND type = %s"
        params.append(vtype)
    if search:
        query += " AND (name LIKE %s OR region LIKE %s OR description LIKE %s)"
        like = f"%{search}%"
        params.extend([like, like, like])

    query += " ORDER BY name ASC"

    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, params)
        rows = cursor.fetchall()
        # Convert Decimal price to int/float for clean JSON
        for r in rows:
            r["price"] = float(r["price"]) if r["price"] is not None else None
        cursor.close()
        conn.close()
        return jsonify(rows)
    except Error as e:
        return jsonify({"error": f"Database error: {e}"}), 500


@app.route("/api/villages/<int:village_id>", methods=["GET"])
def get_village(village_id):
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, name, region, type, description, price, image FROM villages WHERE id = %s",
            (village_id,),
        )
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        if row is None:
            return jsonify({"error": "Village introuvable"}), 404
        row["price"] = float(row["price"]) if row["price"] is not None else None
        return jsonify(row)
    except Error as e:
        return jsonify({"error": f"Database error: {e}"}), 500


VALID_TYPES = ("Montagne", "Désert", "Culturel", "Naturel")


@app.route("/api/villages", methods=["POST"])
def create_village():
    """Admin: add a new attraction/village."""
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    region = (data.get("region") or "").strip()
    vtype = (data.get("type") or "").strip()
    description = (data.get("description") or "").strip()
    image = (data.get("image") or "static/images/hero.png").strip()
    try:
        price = float(data.get("price") or 0)
    except (TypeError, ValueError):
        return jsonify({"error": "Prix invalide."}), 400

    if not all([name, region, vtype, description]):
        return jsonify({"error": "Nom, région, type et description sont obligatoires."}), 400
    if vtype not in VALID_TYPES:
        return jsonify({"error": "Type invalide."}), 400

    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO villages (name, region, type, description, price, image)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (name, region, vtype, description, price, image),
        )
        conn.commit()
        new_id = cursor.lastrowid
        cursor.close()
        conn.close()
        return jsonify({"message": "Attraction ajoutée", "id": new_id}), 201
    except Error as e:
        return jsonify({"error": f"Database error: {e}"}), 500


@app.route("/api/villages/<int:village_id>", methods=["PUT"])
def update_village(village_id):
    """Admin: update an existing attraction/village."""
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    region = (data.get("region") or "").strip()
    vtype = (data.get("type") or "").strip()
    description = (data.get("description") or "").strip()
    image = (data.get("image") or "").strip()
    try:
        price = float(data.get("price") or 0)
    except (TypeError, ValueError):
        return jsonify({"error": "Prix invalide."}), 400

    if not all([name, region, vtype, description]):
        return jsonify({"error": "Nom, région, type et description sont obligatoires."}), 400
    if vtype not in VALID_TYPES:
        return jsonify({"error": "Type invalide."}), 400

    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE villages
            SET name=%s, region=%s, type=%s, description=%s, price=%s,
                image = COALESCE(NULLIF(%s, ''), image)
            WHERE id=%s
            """,
            (name, region, vtype, description, price, image, village_id),
        )
        conn.commit()
        affected = cursor.rowcount
        cursor.close()
        conn.close()
        if affected == 0:
            return jsonify({"error": "Village introuvable"}), 404
        return jsonify({"message": "Attraction mise à jour"})
    except Error as e:
        return jsonify({"error": f"Database error: {e}"}), 500


@app.route("/api/villages/<int:village_id>", methods=["DELETE"])
def delete_village(village_id):
    """Admin: delete an attraction/village."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM villages WHERE id = %s", (village_id,))
        conn.commit()
        affected = cursor.rowcount
        cursor.close()
        conn.close()
        if affected == 0:
            return jsonify({"error": "Village introuvable"}), 404
        return jsonify({"message": "Attraction supprimée"})
    except Error as e:
        return jsonify({"error": f"Database error: {e}"}), 500


# ---------------------------------------------------------------------------
# Admin statistics
# ---------------------------------------------------------------------------
@app.route("/api/stats", methods=["GET"])
def stats():
    """Aggregate data for the admin dashboard charts and counters."""
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT COUNT(*) AS c FROM villages")
        total_villages = cursor.fetchone()["c"]

        cursor.execute("SELECT COUNT(*) AS c FROM reservations")
        total_reservations = cursor.fetchone()["c"]

        # Count attractions grouped by type (for the pie chart)
        cursor.execute("SELECT type, COUNT(*) AS c FROM villages GROUP BY type")
        by_type = {row["type"]: row["c"] for row in cursor.fetchall()}

        # Reservations per month for the current year (for the line chart)
        cursor.execute(
            """
            SELECT MONTH(visit_date) AS m, COUNT(*) AS c
            FROM reservations
            WHERE YEAR(visit_date) = YEAR(CURDATE())
            GROUP BY MONTH(visit_date)
            """
        )
        monthly = [0] * 12
        for row in cursor.fetchall():
            if row["m"]:
                monthly[row["m"] - 1] = row["c"]

        cursor.close()
        conn.close()
        return jsonify(
            {
                "total_villages": total_villages,
                "total_reservations": total_reservations,
                "by_type": by_type,
                "monthly": monthly,
            }
        )
    except Error as e:
        return jsonify({"error": f"Database error: {e}"}), 500


# ---------------------------------------------------------------------------
# Reservations
# ---------------------------------------------------------------------------
@app.route("/api/reservations", methods=["POST"])
def create_reservation():
    data = request.get_json(silent=True) or {}

    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip()
    date = (data.get("date") or "").strip()
    place = (data.get("place") or "").strip()
    visitor_type = (data.get("visitor_type") or "National").strip()

    # Server-side validation
    if not all([name, email, date, place]):
        return jsonify({"error": "Tous les champs sont obligatoires."}), 400
    if "@" not in email or "." not in email:
        return jsonify({"error": "Adresse email invalide."}), 400
    if visitor_type not in ("National", "Étranger"):
        return jsonify({"error": "Type de visiteur invalide."}), 400

    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO reservations (name, email, visit_date, place, visitor_type)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (name, email, date, place, visitor_type),
        )
        conn.commit()
        new_id = cursor.lastrowid
        cursor.close()
        conn.close()
        return jsonify({"message": "Réservation enregistrée", "id": new_id}), 201
    except Error as e:
        return jsonify({"error": f"Database error: {e}"}), 500


@app.route("/api/reservations", methods=["GET"])
def list_reservations():
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT id, name, email, visit_date, place, visitor_type, created_at
            FROM reservations
            ORDER BY created_at DESC
            """
        )
        rows = cursor.fetchall()
        # Stringify dates for JSON
        for r in rows:
            if r.get("visit_date"):
                r["visit_date"] = r["visit_date"].isoformat()
            if r.get("created_at"):
                r["created_at"] = r["created_at"].isoformat()
        cursor.close()
        conn.close()
        return jsonify(rows)
    except Error as e:
        return jsonify({"error": f"Database error: {e}"}), 500


@app.route("/api/reservations/<int:reservation_id>", methods=["DELETE"])
def delete_reservation(reservation_id):
    """Admin: delete a reservation."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM reservations WHERE id = %s", (reservation_id,))
        conn.commit()
        affected = cursor.rowcount
        cursor.close()
        conn.close()
        if affected == 0:
            return jsonify({"error": "Réservation introuvable"}), 404
        return jsonify({"message": "Réservation supprimée"})
    except Error as e:
        return jsonify({"error": f"Database error: {e}"}), 500


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
