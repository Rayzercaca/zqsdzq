from flask import Flask, request, jsonify
from datetime import datetime
import sqlite3

app = Flask(__name__)

DB_NAME = "keys.db"

# =========================
# CREATE DATABASE
# =========================
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS licenses (
        license_key TEXT PRIMARY KEY,
        active INTEGER,
        expires TEXT,
        hwid TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()

# =========================
# HOME PAGE
# =========================
@app.route("/")
def home():
    return "API ONLINE"

# =========================
# CREATE TEST KEY
# =========================
@app.route("/addtest")
def addtest():

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
    INSERT OR REPLACE INTO licenses
    (license_key, active, expires, hwid)
    VALUES (?, ?, ?, ?)
    """, (
        "TEST123",
        1,
        "2027-01-01",
        None
    ))

    conn.commit()
    conn.close()

    return "TEST KEY CREATED"

# =========================
# VERIFY LICENSE
# =========================
@app.route("/verify", methods=["POST"])
def verify():

    data = request.json

    user_key = data.get("key")
    hwid = data.get("hwid")

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
    SELECT active, expires, hwid
    FROM licenses
    WHERE license_key=?
    """, (user_key,))

    result = cursor.fetchone()

    if not result:
        conn.close()
        return jsonify({"status": "invalid"})

    active, expires, saved_hwid = result

    if active == 0:
        conn.close()
        return jsonify({"status": "disabled"})

    if datetime.now() > datetime.fromisoformat(expires):
        conn.close()
        return jsonify({"status": "expired"})

    if saved_hwid is None:

        cursor.execute("""
        UPDATE licenses
        SET hwid=?
        WHERE license_key=?
        """, (hwid, user_key))

        conn.commit()

    elif saved_hwid != hwid:
        conn.close()
        return jsonify({"status": "hwid_mismatch"})

    conn.close()

    return jsonify({"status": "valid"})

# =========================
# RUN
# =========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
