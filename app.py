from flask import Flask, render_template, request, redirect, session, flash
import json, os, datetime

app = Flask(__name__)
app.secret_key = "kp9community-secret-key-change-me"

# ===== Utility =====
def load_json(filename):
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

def save_json(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# ===== Database =====ndef load_users(): return load_json("users.json")
def save_users(data): save_json("users.json", data)
def load_announcements(): return load_json("announcements.json")
def save_announcements(data): save_json("announcements.json", data)
def load_logs(): return load_json("logs.json")
def save_logs(data): save_json("logs.json", data)

# ===== Roles =====
ADMIN_ROLES = ["SO", "head of ADMIN", "head of development"]
ALL_ROLES = ["SO","head of ADMIN","head of development","ADM","DEV","HOA","HOD",
             "VIP","MD","GD","ASDV","HOE","EN","PR","IN"]

# ===== Logging =====
def log_action(actor, action, target=""):
    logs = load_logs()
    logs.append({
        "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "actor": actor,
        "action": action,
        "target": target
    })
    save_logs(logs)

# ===== Routes =====
@app.route("/")
def home():
    if "username" not in session:
        return redirect("/login")
    return redirect("/dashboard")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        users = load_users()
        username = request.form["username"]
        password = request.form["password"]
        user = next((u for u in users if u["username"] == username and u["password"] == password), None)
        if user:
            session["username"] = username
            session["role"] = user["role"]
            flash("เข้าสู่ระบบสำเร็จ", "success")
            return redirect("/dashboard")
        flash("ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง", "danger")
    return render_template("login.html")

@app.route("/dashboard")
def dashboard():
    if "username" not in session:
        return redirect("/login")
    users = load_users()
    current_user = next((u for u in users if u["username"] == session["username"]), None)
    announcements = load_announcements()
    # counts
    total_users = len(users)
    total_ann = len(announcements)
    logs = load_logs()
    recent_logs = logs[-5:][::-1]
    return render_template("dashboard.html", user=current_user, users=users, announcements=announcements, total_users=total_users, total_ann=total_ann, recent_logs=recent_logs)

@app.route("/profile/<username>")
def profile(username):
    if "username" not in session:
        return redirect("/login")
    users = load_users()
    target = next((u for u in users if u["username"] == username), None)
    if not target:
        return "ไม่พบผู้ใช้", 404
    return render_template("profile.html", user=target)

# ===== Manage Users =====
@app.route("/manage", methods=["GET", "POST"])
def manage_users():
    if "username" not in session: return redirect("/login")
    role = session["role"]
    if role not in ADMIN_ROLES: return "คุณไม่มีสิทธิ์เข้าถึงหน้านี้", 403

    users = load_users()

    if request.method == "POST":
        action = request.form.get("action")
        if action == "add":
            new_user = {
                "username": request.form["username"].strip(),
                "password": request.form["password"],
                "name": request.form["name"],
                "role": request.form["role"]
            }
            # basic duplication check
            if any(u["username"] == new_user["username"] for u in users):
                flash("มีชื่อผู้ใช้นี้อยู่แล้ว", "danger")
            else:
                users.append(new_user)
                save_users(users)
                log_action(session["username"], "เพิ่มผู้ใช้", new_user["username"])
                flash("เพิ่มผู้ใช้เรียบร้อยแล้ว", "success")

        elif action == "delete":
            uname = request.form["username"]
            users = [u for u in users if u["username"] != uname]
            save_users(users)
            log_action(session["username"], "ลบผู้ใช้", uname)
            flash("ลบผู้ใช้เรียบร้อยแล้ว", "info")

        elif action == "edit":
            uname = request.form["username"]
            for u in users:
                if u["username"] == uname:
                    u["name"] = request.form["name"]
                    u["role"] = request.form["role"]
                    if request.form.get("password"):
                        u["password"] = request.form["password"]
                    log_action(session["username"], "แก้ไขข้อมูล", uname)
            save_users(users)
            flash("แก้ไขข้อมูลผู้ใช้เรียบร้อยแล้ว", "warning")

    return render_template("manage_users.html", users=users, all_roles=ALL_ROLES)

# ===== Announcements =====
@app.route("/announcements", methods=["GET", "POST"])
def announcements():
    if "username" not in session: return redirect("/login")
    announcements = load_announcements()
    role = session["role"]

    if request.method == "POST" and role in ADMIN_ROLES:
        action = request.form.get("action")
        if action == "add":
            new_announce = {
                "title": request.form["title"],
                "content": request.form["content"],
                "author": session["username"],
                "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            announcements.append(new_announce)
            save_announcements(announcements)
            log_action(session["username"], "เพิ่มประกาศ", request.form["title"])
            flash("เพิ่มประกาศแล้ว", "success")
        elif action == "delete":
            title = request.form["title"]
            announcements = [a for a in announcements if a["title"] != title]
            save_announcements(announcements)
            log_action(session["username"], "ลบประกาศ", title)
            flash("ลบประกาศเรียบร้อยแล้ว", "info")

    return render_template("announcements.html", announcements=announcements, role=role)

# ===== Logs =====
@app.route("/logs")
def logs_view():
    if "username" not in session:
        return redirect("/login")
    if session["role"] not in ADMIN_ROLES:
        return "คุณไม่มีสิทธิ์ดู Log", 403
    logs = load_logs()[::-1]
    return render_template("logs.html", logs=logs)

@app.route("/logout")
def logout():
    session.clear()
    flash("ออกจากระบบแล้ว", "info")
    return redirect("/login")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
