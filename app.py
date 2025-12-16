from flask import Flask, render_template, request, redirect, session, flash, url_for
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
import pathlib
from flask import g
import os
from openai import OpenAI 

app = Flask(__name__)
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

app.secret_key = "mysecretkey"

DB_PATH = "expenses.db"


# ----------- DB CONNECTION -------------
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ----------- INIT DB (Flask 3.x safe) -------------
def init_db():
    
    conn = get_db()
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        email TEXT UNIQUE,
        password TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        amount REAL,
        category TEXT,
        date TEXT,
        note TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS income (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        amount REAL,
        category TEXT,
        date TEXT,
        note TEXT
    )
    """)
    conn.execute("""
CREATE TABLE IF NOT EXISTS reminders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    title TEXT,
    amount REAL,
    due_date TEXT,
    status TEXT DEFAULT 'pending'
)
""")
    conn.execute("""
CREATE TABLE IF NOT EXISTS rewards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    badge TEXT,
    date TEXT
)
""")

    conn.commit()
    conn.close()


# Run DB init once at startup
with app.app_context():
    init_db()
# after init_db() definition and DB init block

def ensure_profile_column():
    conn = get_db()
    cur = conn.cursor()
    # Check if column exists
    cur.execute("PRAGMA table_info(users)")
    cols = [r["name"] for r in cur.fetchall()]
    if "profile_image" not in cols:
        try:
            cur.execute("ALTER TABLE users ADD COLUMN profile_image TEXT")
            conn.commit()
        except Exception as e:
            # SQLite may fail in some environments; ignore if so
            print("Could not add profile_image column:", e)
    conn.close()

# call once at startup (keep with app.app_context() init)
with app.app_context():
    init_db()
    ensure_profile_column()


# ----------- AUTH -------------
@app.route("/")
def index():
    if "user_id" in session:
        return redirect("/dashboard")
    return redirect("/login")


@app.route('/signup', methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form["username"]
        email = request.form["email"]
        pwd = generate_password_hash(request.form["password"])

        conn = get_db()
        try:
            conn.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                         (name, email, pwd))
            conn.commit()
            flash("Account created! Please login.")
            return redirect("/login")
        except:
            flash("Email already exists!")
        finally:
            conn.close()

    return render_template("signup.html")


@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        pwd = request.form["password"]

        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
        conn.close()

        if user and check_password_hash(user["password"], pwd):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            return redirect("/dashboard")

        flash("Invalid email or password")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# ----------- ADD EXPENSE -------------
@app.route('/add', methods=["GET", "POST"])
def add_expense():
    if "user_id" not in session:
        return redirect("/login")

    if request.method == "POST":
        uid = session["user_id"]
        amt = request.form["amount"]
        cat = request.form["category"]
        date = request.form["date"]
        note = request.form["note"]

        conn = get_db()
        conn.execute("INSERT INTO expenses (user_id, amount, category, date, note) VALUES (?, ?, ?, ?, ?)",
                     (uid, amt, cat, date, note))
        conn.commit()
        conn.close()

        flash("Expense added!")
        return redirect("/dashboard")

    return render_template("add_expense.html", expense=None)


# ----------- EDIT EXPENSE -------------
@app.route('/edit/<int:id>', methods=["GET", "POST"])
def edit_expense(id):
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()
    row = conn.execute("SELECT * FROM expenses WHERE id=? AND user_id=?", (id, session["user_id"])).fetchone()

    if not row:
        conn.close()
        flash("Expense not found!")
        return redirect("/dashboard")

    if request.method == "POST":
        amt = request.form["amount"]
        cat = request.form["category"]
        date = request.form["date"]
        note = request.form["note"]

        conn.execute("UPDATE expenses SET amount=?, category=?, date=?, note=? WHERE id=?",
                     (amt, cat, date, note, id))
        conn.commit()
        conn.close()

        flash("Expense updated!")
        return redirect("/dashboard")

    conn.close()
    return render_template("add_expense.html", expense=row)


@app.route('/delete/<int:id>')
def delete_expense(id):
    conn = get_db()
    conn.execute("DELETE FROM expenses WHERE id=? AND user_id=?", (id, session["user_id"]))
    conn.commit()
    conn.close()

    flash("Expense deleted!")
    return redirect("/dashboard")


# ----------- ADD INCOME -------------
@app.route('/income/add', methods=["GET", "POST"])
def add_income():
    if "user_id" not in session:
        return redirect("/login")

    if request.method == "POST":
        uid = session["user_id"]
        amt = request.form["amount"]
        cat = request.form["category"]
        date = request.form["date"]
        note = request.form["note"]

        conn = get_db()
        conn.execute("INSERT INTO income (user_id, amount, category, date, note) VALUES (?, ?, ?, ?, ?)",
                     (uid, amt, cat, date, note))
        conn.commit()
        conn.close()

        flash("Income added!")
        return redirect("/dashboard")

    return render_template("add_income.html")


# ----------- EXPENSE LIST PAGE ----------
@app.route('/expenses')
def expense_list():
    if "user_id" not in session:
        return redirect("/login")

    uid = session["user_id"]
    conn = get_db()
    rows = conn.execute("SELECT * FROM expenses WHERE user_id=? ORDER BY date DESC", (uid,)).fetchall()
    conn.close()
    return render_template("expense_list.html", expenses=rows)


# ----------- DASHBOARD -------------
@app.route('/dashboard')
def dashboard():
    if "user_id" not in session:
        return redirect("/login")

    uid = session["user_id"]
    conn = get_db()

    # Total expenses & income
    total_expense = conn.execute(
        "SELECT IFNULL(SUM(amount),0) FROM expenses WHERE user_id=?", (uid,)
    ).fetchone()[0]

    total_income = conn.execute(
        "SELECT IFNULL(SUM(amount),0) FROM income WHERE user_id=?", (uid,)
    ).fetchone()[0]

    balance = total_income - total_expense

    # THIS MONTH EXPENSE
    month_total = conn.execute("""
        SELECT IFNULL(SUM(amount),0) 
        FROM expenses
        WHERE user_id=?
        AND strftime('%Y-%m', date) = strftime('%Y-%m', 'now')
    """, (uid,)).fetchone()[0]

    # DAILY AVERAGE
    daily_avg = conn.execute("""
        SELECT IFNULL(AVG(amount),0)
        FROM expenses
        WHERE user_id=?
    """, (uid,)).fetchone()[0]

    # Category pie chart
    rows = conn.execute("""
        SELECT category, SUM(amount)
        FROM expenses
        WHERE user_id=?
        GROUP BY category
    """, (uid,)).fetchall()

    cat_labels = [r[0] for r in rows]
    cat_values = [r[1] for r in rows]

    # Monthly bar chart
    m = conn.execute("""
        SELECT strftime('%Y-%m', date), SUM(amount)
        FROM expenses
        WHERE user_id=?
        GROUP BY strftime('%Y-%m', date)
        ORDER BY 1 ASC
    """, (uid,)).fetchall()

    month_labels = [r[0] for r in m]
    month_values = [r[1] for r in m]

    # Recent activities (income + expenses)
    recent_exp = conn.execute("""
        SELECT id, date, category, note, amount, 'Expense' AS type
        FROM expenses
        WHERE user_id=?
    """, (uid,)).fetchall()

    recent_inc = conn.execute("""
        SELECT id, date, category, note, amount, 'Income' AS type
        FROM income
        WHERE user_id=?
    """, (uid,)).fetchall()

    # merge and sort recent activities (newest first)
    recent_all = sorted(
        list(recent_exp) + list(recent_inc),
        key=lambda r: r["date"],
        reverse=True
    )

    # fetch all reminders sorted by nearest due date
    reminders = conn.execute("""
    SELECT * FROM reminders
    WHERE user_id=?
    ORDER BY due_date ASC
    LIMIT 5
""", (uid,)).fetchall()

    # check due reminders within 3 days
    due_popup = conn.execute("""
    SELECT title, due_date
    FROM reminders
    WHERE user_id=? 
    AND status='pending'
    AND DATE(due_date) <= DATE('now', '+3 day')
    AND DATE(due_date) >= DATE('now')
    ORDER BY due_date ASC
    LIMIT 1
    """, (uid,)).fetchone()

    conn.close()

    return render_template(
        "dashboard.html",
        username=session["username"],
        total=total_expense,
        income_total=total_income,
        balance=balance,
        month_total=month_total,
        daily_avg=daily_avg,
        cat_labels=cat_labels,
        cat_values=cat_values,
        month_labels=month_labels,
        month_values=month_values,
        recent=recent_all,
        due_popup=due_popup,
        reminders=reminders
    )
UPLOAD_DIR = os.path.join("static", "images", "profiles")
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_EXT = {'png','jpg','jpeg','webp','gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.',1)[1].lower() in ALLOWED_EXT

@app.route('/profile', methods=['GET','POST'])
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    uid = session['user_id']
    conn = get_db()

    # handle profile update (name, email, username, avatar)
    if request.method == 'POST' and request.form.get('form-type') == 'profile':
        username = request.form.get('username','').strip()
        email = request.form.get('email','').strip().lower()
        fname = request.form.get('first_name','').strip()
        lname = request.form.get('last_name','').strip()

        # handle avatar upload
        file = request.files.get('avatar')
        avatar_filename = None
        if file and file.filename and allowed_file(file.filename):
            fname_clean = secure_filename(file.filename)
            ext = pathlib.Path(fname_clean).suffix
            avatar_filename = f"profile_{uid}{ext}"
            save_path = os.path.join(UPLOAD_DIR, avatar_filename)
            file.save(save_path)

            # store relative path (static path)
            db_path = f"images/profiles/{avatar_filename}"
            conn.execute("UPDATE users SET profile_image = ? WHERE id = ?", (db_path, uid))

        # update other fields
        conn.execute("UPDATE users SET username = ?, email = ?, profile_image = COALESCE(profile_image, profile_image) WHERE id = ?",
                     (username, email, uid))
        conn.commit()
        flash("Profile updated")
        # refresh session username
        session['username'] = username
        conn.close()
        return redirect(url_for('profile'))

    # handle password update
    if request.method == 'POST' and request.form.get('form-type') == 'password':
        current = request.form.get('current_password','')
        newp = request.form.get('new_password','')
        confirm = request.form.get('confirm_password','')

        user = conn.execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone()
        if not user or not check_password_hash(user['password'], current):
            flash("Current password is incorrect")
            conn.close()
            return redirect(url_for('profile'))

        if not newp or newp != confirm:
            flash("New passwords do not match")
            conn.close()
            return redirect(url_for('profile'))

        new_hash = generate_password_hash(newp)
        conn.execute("UPDATE users SET password=? WHERE id=?", (new_hash, uid))
        conn.commit()
        conn.close()
        flash("Password updated successfully")
        return redirect(url_for('profile'))

    # GET: fetch user
    user = conn.execute("SELECT id, username, email, profile_image FROM users WHERE id=?", (uid,)).fetchone()
    conn.close()

    # Use a fallback image (from your uploads) if none set
    default_avatar = "/mnt/data/A_3D-rendered_digital_illustration_features_a_prof.png"
    avatar_url = url_for('static', filename=user['profile_image']) if user['profile_image'] else default_avatar

    return render_template("profile.html", user=user, avatar_url=avatar_url)

@app.context_processor
def inject_avatar():
    if "user_id" not in session:
        return {"avatar_url": url_for("static", filename="images/default_profile.png")}
    conn = get_db()
    user = conn.execute("SELECT profile_image FROM users WHERE id=?", (session["user_id"],)).fetchone()
    conn.close()
    if user and user["profile_image"]:
        return {"avatar_url": url_for("static", filename=user["profile_image"])}
    return {"avatar_url": url_for("static", filename="images/default_profile.png")}
@app.context_processor
def inject_avatar():
    # default avatar
    default = url_for("static", filename="images/default_profile.png")

    if "user_id" not in session:
        return {"avatar_url": default}

    conn = get_db()
    user = conn.execute("SELECT profile_image FROM users WHERE id=?", (session["user_id"],)).fetchone()
    conn.close()

    if user and user["profile_image"]:
        return {"avatar_url": url_for("static", filename=user["profile_image"])}
    return {"avatar_url": default}
from openai import OpenAI
client = OpenAI(api_key="sk-abcdef1234567890abcdef1234567890abcdef12")   # replace

@app.post("/api/chat")
def api_chat():
    data = request.get_json()
    msg = data.get("message", "")

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a friendly helpful assistant."},
            {"role": "user", "content": msg}
        ]
    )

    reply = response.choices[0].message.content
    return {"reply": reply}
@app.route("/reminder/add", methods=["GET", "POST"])
def add_reminder():
    if "user_id" not in session:
        return redirect("/login")

    if request.method == "POST":
        title = request.form["title"]
        amount = request.form["amount"]
        due_date = request.form["due_date"]

        conn = get_db()
        conn.execute("INSERT INTO reminders (user_id, title, amount, due_date) VALUES (?, ?, ?, ?)",
                     (session["user_id"], title, amount, due_date))
        conn.commit()
        conn.close()

        flash("Reminder added successfully!")
        return redirect("/reminders")

    return render_template("add_reminder.html")
@app.route("/reminders")
def reminders():
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()
    rows = conn.execute("SELECT * FROM reminders WHERE user_id=? ORDER BY due_date ASC",
                        (session["user_id"],)).fetchall()
    conn.close()

    return render_template("reminders.html", reminders=rows)
@app.route("/reminder/delete/<int:id>")
def delete_reminder(id):
    conn = get_db()
    conn.execute("DELETE FROM reminders WHERE id=? AND user_id=?", (id, session["user_id"]))
    conn.commit()
    conn.close()
    flash("Reminder removed")
    return redirect("/reminders")
@app.route("/help")
def help_center():
    return render_template("help_center.html")

@app.route("/privacy")
def privacy_policy():
    return render_template("privacy_policy.html")

@app.route("/terms")
def terms_of_use():
    return render_template("terms_of_use.html")
if __name__ == "__main__":
    app.run(debug=True)
# configure upload folder (near top of app.py)

