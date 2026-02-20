import sqlite3
from pathlib import Path

from flask import Flask, redirect, render_template, request, url_for

app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "db.sqlite3"


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS flames_result (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                your_name TEXT NOT NULL,
                crush_name TEXT NOT NULL,
                result TEXT NOT NULL
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


def calculate_flames_result(your_name: str, crush_name: str) -> str:
    # Keep only letters and normalize for matching.
    your_chars = [ch for ch in your_name.lower() if ch.isalpha()]
    crush_chars = [ch for ch in crush_name.lower() if ch.isalpha()]

    # Remove common letters (single occurrence each time).
    i = 0
    while i < len(your_chars):
        ch = your_chars[i]
        if ch in crush_chars:
            your_chars.pop(i)
            crush_chars.remove(ch)
        else:
            i += 1

    count = len(your_chars) + len(crush_chars)
    if count == 0:
        return "Friends"

    flames = ["Friends", "Love", "Affection", "Marriage", "Enemy", "Sibling"]
    index = 0
    while len(flames) > 1:
        index = (index + count - 1) % len(flames)
        flames.pop(index)

    return flames[0]


init_db()


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/result", methods=["POST"])
def result():
    your_name = request.form.get("your_name", "").strip()
    crush_name = request.form.get("crush_name", "").strip()

    if not your_name or not crush_name:
        return redirect(url_for("index"))

    conn = get_db_connection()
    try:
        row = conn.execute(
            "SELECT result FROM flames_result WHERE your_name=? AND crush_name=? LIMIT 1",
            (your_name, crush_name),
        ).fetchone()

        if row:
            final_result = row["result"]
        else:
            final_result = calculate_flames_result(your_name, crush_name)
            conn.execute(
                "INSERT INTO flames_result (your_name, crush_name, result) VALUES (?, ?, ?)",
                (your_name, crush_name, final_result),
            )
            conn.commit()
    finally:
        conn.close()

    return render_template(
        "result.html",
        your_name=your_name,
        crush_name=crush_name,
        result=final_result,
    )


@app.route("/result", methods=["GET"])
def result_get():
    return redirect(url_for("index"))


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
