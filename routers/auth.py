
from flask import Blueprint, request, jsonify
import sqlite3
import os
import re

from werkzeug.security import generate_password_hash, check_password_hash


auth = Blueprint("auth", __name__)


# =========================
# DATABASE PATH
# =========================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATABASE = os.path.join(
    BASE_DIR,
    "database",
    "expense_splitter.db"
)


# =========================
# DATABASE CONNECTION
# =========================

def get_connection():

    connection = sqlite3.connect(DATABASE)

    connection.row_factory = sqlite3.Row

    connection.execute("PRAGMA foreign_keys = ON")

    return connection


# =========================
# REGISTER
# =========================

@auth.route("/register", methods=["POST"])
def register():

    data = request.get_json(silent=True)

    if not data:
        return jsonify({
            "message": "Invalid request"
        }), 400

    name = data.get("name", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not name or not email or not password:

        return jsonify({
            "message": "All fields are required"
        }), 400

    if len(password) < 6:

        return jsonify({
            "message": "Password must contain at least 6 characters"
        }), 400

    password_hash = generate_password_hash(password)

    connection = get_connection()

    try:

        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO users (name, email, password)
            VALUES (?, ?, ?)
            """,
            (name, email, password_hash)
        )

        connection.commit()

        return jsonify({
            "message": "Registration successful"
        }), 201

    except sqlite3.IntegrityError:

        return jsonify({
            "message": "Email already registered"
        }), 400

    except sqlite3.Error:

        return jsonify({
            "message": "Database error during registration"
        }), 500

    finally:

        connection.close()


# =========================
# LOGIN
# =========================

@auth.route("/login", methods=["POST"])
def login():

    data = request.get_json(silent=True)

    if not data:

        return jsonify({
            "message": "Invalid request"
        }), 400

    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not email or not password:

        return jsonify({
            "message": "Email and password are required"
        }), 400

    connection = get_connection()

    try:

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT id, name, email, password
            FROM users
            WHERE LOWER(email) = ?
            """,
            (email,)
        )

        user = cursor.fetchone()

    except sqlite3.Error:

        return jsonify({
            "message": "Database error during login"
        }), 500

    finally:

        connection.close()

    if user is None:

        return jsonify({
            "message": "Invalid email or password"
        }), 401

    try:

        if check_password_hash(user["password"], password):

            return jsonify({
                "message": "Login successful",

                # Compatible with index.html
                "user_id": user["id"],
                "name": user["name"],
                "email": user["email"],

                # Also provide nested user information
                "user": {
                    "id": user["id"],
                    "name": user["name"],
                    "email": user["email"]
                }
            }), 200

    except (ValueError, TypeError):

        pass

    return jsonify({
        "message": "Invalid email or password"
    }), 401


# =========================
# GET ALL USERS
# =========================

@auth.route("/users", methods=["GET"])
def get_users():

    connection = get_connection()

    try:

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT id, name, email
            FROM users
            ORDER BY name
            """
        )

        users = cursor.fetchall()

        user_list = []

        for user in users:

            user_list.append({
                "id": user["id"],
                "name": user["name"],
                "email": user["email"]
            })

        return jsonify({
            "users": user_list
        }), 200

    except sqlite3.Error:

        return jsonify({
            "message": "Unable to fetch users"
        }), 500

    finally:

        connection.close()


# =========================
# SAVE / UPDATE UPI ID
# =========================

@auth.route("/users/<int:user_id>/upi", methods=["POST"])
def update_upi_id(user_id):

    data = request.get_json(silent=True)

    if not data:

        return jsonify({
            "message": "Invalid request"
        }), 400

    upi_id = data.get("upi_id", "").strip()

    if not upi_id:

        return jsonify({
            "message": "UPI ID is required"
        }), 400

    # Basic UPI ID format validation

    pattern = r"^[a-zA-Z0-9._-]+@[a-zA-Z0-9]+$"

    if not re.match(pattern, upi_id):

        return jsonify({
            "message": "Please enter a valid UPI ID"
        }), 400

    connection = get_connection()

    try:

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT id
            FROM users
            WHERE id = ?
            """,
            (user_id,)
        )

        user = cursor.fetchone()

        if user is None:

            return jsonify({
                "message": "User not found"
            }), 404

        cursor.execute(
            """
            UPDATE users
            SET upi_id = ?
            WHERE id = ?
            """,
            (upi_id, user_id)
        )

        connection.commit()

        return jsonify({
            "message": "UPI ID saved successfully"
        }), 200

    except sqlite3.Error:

        return jsonify({
            "message": "Unable to save UPI ID"
        }), 500

    finally:

        connection.close()


# =========================
# GET USER UPI ID
# =========================

@auth.route("/users/<int:user_id>/upi", methods=["GET"])
def get_upi_id(user_id):

    connection = get_connection()

    try:

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT upi_id
            FROM users
            WHERE id = ?
            """,
            (user_id,)
        )

        user = cursor.fetchone()

        if user is None:

            return jsonify({
                "message": "User not found"
            }), 404

        return jsonify({
            "upi_id": user["upi_id"] or ""
        }), 200

    except sqlite3.Error:

        return jsonify({
            "message": "Unable to fetch UPI ID"
        }), 500

    finally:

        connection.close()
