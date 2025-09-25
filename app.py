from flask import Flask, render_template, request, redirect, url_for, session
from flask import session
from db import create_client
from supabase import create_client, Client
from werkzeug.security import check_password_hash, generate_password_hash
import os

app = Flask(__name__)

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

app.secret_key = "dev123"

supabase = create_client(url, key)


@app.route("/", methods=["GET", "POST"])
def upload():
    if "user_id" not in session:
        return redirect(url_for("login"))

    # normal upload logic...
    return render_template("index.html")


@app.route("/analytics", methods=["GET","POST"])
def analytics():
    return render_template("analytics.html")

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