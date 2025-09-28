from flask import Flask, render_template, request, redirect, url_for, session
from flask import session, jsonify
from db import create_client
from supabase import create_client, Client
from werkzeug.security import check_password_hash, generate_password_hash
import os
import tempfile
from pipeline import run_pipeline
import threading


app = Flask(__name__)

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

app.secret_key = "dev123"

supabase = create_client(url, key)

jobs = {}

def run_in_background(file_path, user_id):
    run_pipeline(file_path, user_id)
    jobs[user_id] = "done"


@app.route("/", methods=["GET", "POST"])
def upload():
    # 1. Make sure user is logged in
    if not session.get("user_id"):
        return redirect(url_for("login"))

    # 2. Check if hero is linked
    user = (
        supabase.table("users")
        .select("hero_player_id")
        .eq("id", session["user_id"])
        .execute()
    ).data[0]

    if not user["hero_player_id"]:
        return redirect(url_for("profile"))  # force them to link first

    if request.method == "POST":
        action = request.form.get("action")
        text_data = None

        if action == "file":
            file = request.files.get("file_input")
            if file and file.filename:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as tmp:
                    file.save(tmp.name)
                    jobs[session["user_id"]] = "processing"
                    threading.Thread(
                        target=run_in_background, 
                        args=(tmp.name, session["user_id"])
                    ).start()
                return redirect(url_for("processing"))

        elif action == "paste":
            text_data = request.form.get("paste_input")
            if text_data:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".txt", mode="w") as tmp:
                    tmp.write(text_data)
                    jobs[session["user_id"]] = "processing"
                    threading.Thread(
                        target=run_in_background, 
                        args=(tmp.name, session["user_id"])
                    ).start()
                return redirect(url_for("processing"))

        return "No data received", 400

    return render_template("upload.html")

@app.route("/processing")
def processing():
    if jobs.get(session["user_id"]) == "done":
        return redirect(url_for("analytics"))
    return render_template("processing.html")


from datetime import datetime

@app.route("/analytics")
def analytics():
    if not session.get("user_id"):
        return redirect(url_for("login"))

    # sessions
    res = supabase.rpc("get_user_sessions", {"uid": session["user_id"]}).execute()
    sessions_data = res.data or []

    # overall stats
    res2 = supabase.rpc("get_user_overall", {"uid": session["user_id"]}).execute()
    overall = res2.data[0] if res2.data else {"sessions": 0, "hands": 0, "vpip": None}

    # format session dates
    from datetime import datetime
    for s in sessions_data:
        raw = s.get("started_at")
        if raw:
            try:
                dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
                s["started_at"] = dt.strftime("%Y-%m-%d %H:%M")
            except Exception:
                pass

    user_stats_res = supabase.rpc("get_user_stats", {"uid": session["user_id"]}).execute()
    user_stats = user_stats_res.data[0] if user_stats_res.data else {
        "play_time": None,
        "amount": 0,
        "hourly_rate": None
    }


    return render_template("analytics.html", sessions=sessions_data, overall=overall, user_stats=user_stats)





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
            session["hero_player_id"] = user.get("hero_player_id") 
            return redirect(url_for("upload"))
        else:
            return "Invalid credentials", 401

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/profile", methods=["GET", "POST"])
def profile():
    if request.method == "POST":
        # Handle unlink
        if "unlink" in request.form:
            supabase.table("users").update({"hero_player_id": None}).eq("id", session["user_id"]).execute()
            return redirect(url_for("profile"))

        # Handle linking
        hero_name = request.form.get("hero_name")
        if hero_name:
            res = supabase.table("poker_players").select("id").eq("name", hero_name).execute()

            if res.data:
                hero_id = res.data[0]["id"]
            else:
                hero = supabase.table("poker_players").insert({"name": hero_name}).execute()
                hero_id = hero.data[0]["id"]

            supabase.table("users").update({"hero_player_id": hero_id}).eq("id", session["user_id"]).execute()
            return redirect(url_for("profile"))

    user = (
        supabase.table("users")
        .select("username, hero_player_id")
        .eq("id", session["user_id"])
        .execute()
    ).data[0]

    hero_name = None
    if user["hero_player_id"]:
        res = (
            supabase.table("poker_players")
            .select("name")
            .eq("id", user["hero_player_id"])
            .execute()
        )
        if res.data:
            hero_name = res.data[0]["name"]

    return render_template("profile.html", user=user, hero_name=hero_name)
@app.route("/session_summary/<int:sid>")
def session_summary(sid):
    if not session.get("user_id"):
        return redirect(url_for("login"))

    # All sessions for the right-hand table
    res = supabase.rpc("get_user_sessions", {"uid": session["user_id"]}).execute()
    sessions_data = res.data or []

    # Look up hero_player_id fresh from DB
    user_res = supabase.table("users").select("hero_player_id").eq("id", session["user_id"]).execute()
    hero_id = user_res.data[0]["hero_player_id"] if user_res.data else None

    stats = {"hands": 0, "vpip": None, "pfr": None}
    if hero_id:
        res2 = supabase.rpc("get_session_overall", {"sid": sid, "hero_id": hero_id}).execute()
        if res2.data:
            stats = res2.data[0]

    # Format session dates
    from datetime import datetime
    for s in sessions_data:
        raw = s.get("started_at")
        if raw:
            try:
                dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
                s["started_at"] = dt.strftime("%Y-%m-%d %H:%M")
            except Exception:
                pass


    stats_res = supabase.rpc("get_session_stats", {
        "sid": sid,
        "hero_id": hero_id
    }).execute()

    session_stats = stats_res.data[0] if stats_res.data else {
        "play_time": None,
        "amount": 0,
        "hourly_rate": None
    }

    bankroll_res = supabase.rpc("get_session_bankroll", {
        "sid": sid,
        "hero_id": hero_id
    }).execute()

    bankroll_data = bankroll_res.data or []



    return render_template(
        "session_summary.html",
        sessions=sessions_data,
        overall=stats,
        selected_session=sid,
        bankroll_data=bankroll_data,
        session_stats=session_stats
    )




if __name__ == "__main__":
    app.run(debug=True)