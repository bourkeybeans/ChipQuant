from flask import Flask, render_template, request, redirect, url_for, session
from flask import session
from db import create_client
from supabase import create_client, Client
from werkzeug.security import check_password_hash, generate_password_hash
import os
from pipeline import run_pipeline

app = Flask(__name__)

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

app.secret_key = "dev123"

supabase = create_client(url, key)


@app.route("/", methods=["GET", "POST"])
def index():
    if not session.get("user_id"):
        return redirect(url_for("login"))
    
    text_data = None

    if request.method == "POST":
        action = request.form.get("action")

        if action == "file":
            file = request.files.get("file_input")
            if file:
                text_data = file.read().decode("utf-8")

        elif action == "paste":
            text_data = request.form.get("paste_input")

        if text_data:
            run_pipeline(text_data, session.get("user_id"))

    return render_template("index.html")


@app.route("/analytics", methods=["POST"])
def analytics():
    action = request.form.get("action")

    if action == "file":
        file = request.files.get("file_input")
        if file:
            data = file.read().decode("utf-8")
            # process uploaded file here
    elif action == "paste":
        data = request.form.get("paste_input")
        # process pasted text here

    return render_template("analytics.html", data_preview=data[:200])

@app.route("/profile")
def profile():
    # Example: pass a user object
    user = {"username": "Fin"}
    return render_template("profile.html", user=user)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        hash_pw = generate_password_hash(password)
        supabase.table("users").insert({
            "username": username,
            "email": email,
            "password_hash": hash_pw
        }).execute()

        return redirect(url_for("login"))

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        res = supabase.table("users").select("*").eq("email", email).execute()
        if len(res.data) == 0:
            return "Invalid credentials", 401

        user = res.data[0]
        if check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            return redirect(url_for("upload"))
        else:
            return "Invalid credentials", 401

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)