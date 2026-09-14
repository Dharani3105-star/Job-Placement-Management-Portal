from flask import Flask, render_template, request, redirect, session 
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

app.secret_key = os.environ.get("SECRET_KEY", "development-secret-key")

ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD")


# ---------------- DATABASE ----------------
def get_db():

    os.makedirs(app.instance_path, exist_ok=True)

    db_path = os.path.join(app.instance_path, "placement.db")

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    return conn




def init_db():

    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            job TEXT NOT NULL,
            company TEXT NOT NULL,
            location TEXT NOT NULL,
            status TEXT NOT NULL,
            applied_at TEXT NOT NULL
        )
    """)
        # Add resume column to existing applications table
    try:
        conn.execute(
            "ALTER TABLE applications ADD COLUMN resume TEXT"
        )
    except sqlite3.OperationalError:
        # Column already exists
        pass

    conn.commit()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            company TEXT NOT NULL,
            location TEXT NOT NULL
        )
    """)

        # Add job description column if it does not exist
    try:
        conn.execute(
            "ALTER TABLE jobs ADD COLUMN description TEXT"
        )
    except sqlite3.OperationalError:
        pass

    # Add required skills column if it does not exist
    try:
        conn.execute(
            "ALTER TABLE jobs ADD COLUMN skills TEXT"
        )
    except sqlite3.OperationalError:
        pass

    # Add eligibility column if it does not exist
    try:
        conn.execute(
            "ALTER TABLE jobs ADD COLUMN eligibility TEXT"
        )
    except sqlite3.OperationalError:
        pass

    conn.commit()
            # Add applied_at column to existing database if it doesn't exist
    try:
        conn.execute(
            "ALTER TABLE applications ADD COLUMN applied_at TEXT"
        )
        conn.commit()
    except sqlite3.OperationalError:
        # Column already exists
        pass
    # Add current date/time to old applications
    conn.execute(
        """
        UPDATE applications
        SET applied_at = datetime('now')
        WHERE applied_at IS NULL
        """
    )

    conn.commit()

        # Add details to existing jobs
    conn.execute(
        """
        UPDATE jobs
        SET description = ?,
            skills = ?,
            eligibility = ?
        WHERE title = 'Python Developer Intern'
        """,
        (
            "Develop and maintain Python applications and backend features.",
            "Python, Flask, SQL",
            "B.Tech / B.E students"
        )
    )

    conn.execute(
        """
        UPDATE jobs
        SET description = ?,
            skills = ?,
            eligibility = ?
        WHERE title = 'Web Developer Intern'
        """,
        (
            "Build and maintain responsive web applications.",
            "HTML, CSS, JavaScript, Flask",
            "B.Tech / B.E students"
        )
    )

    conn.execute(
        """
        UPDATE jobs
        SET description = ?,
            skills = ?,
            eligibility = ?
        WHERE title = 'Data Analyst Intern'
        """,
        (
            "Analyze datasets and create useful business insights and reports.",
            "Python, Pandas, SQL, Excel",
            "B.Tech / B.E students"
        )
    )

    conn.commit()

        # Add default jobs if jobs table is empty
    job_count = conn.execute(
        "SELECT COUNT(*) FROM jobs"
    ).fetchone()[0]

    if job_count == 0:
        conn.execute(
            "INSERT INTO jobs (title, company, location) VALUES (?, ?, ?)",
            ("Python Developer Intern", "Tech Solutions", "Hyderabad")
        )

        conn.execute(
            "INSERT INTO jobs (title, company, location) VALUES (?, ?, ?)",
            ("Web Developer Intern", "WebWorks", "Bangalore")
        )

        conn.execute(
            "INSERT INTO jobs (title, company, location) VALUES (?, ?, ?)",
            ("Data Analyst Intern", "DataTech", "Chennai")
        )

        conn.commit()

    conn.close()



# Store registered students
students = []

# Available jobs
jobs = [
    {
        "id": 1,
        "title": "Python Developer Intern",
        "company": "Tech Solutions",
        "location": "Hyderabad"
    },
    {
        "id": 2,
        "title": "Web Developer Intern",
        "company": "WebWorks",
        "location": "Bangalore"
    },
    {
        "id": 3,
        "title": "Data Analyst Intern",
        "company": "DataTech",
        "location": "Chennai"
    }
]

# Store job applications
applications = []


# ---------------- HOME PAGE ----------------

@app.route("/")
def home():

    if "student" not in session:
        return redirect("/login")

    search = request.args.get("search", "").strip().lower()

    conn = get_db()

    if search:
        job_list = conn.execute(
            """
            SELECT * FROM jobs
            WHERE LOWER(title) LIKE ?
            OR LOWER(company) LIKE ?
            OR LOWER(location) LIKE ?
            """,
            (
                "%" + search + "%",
                "%" + search + "%",
                "%" + search + "%"
            )
        ).fetchall()
    else:
        job_list = conn.execute(
            "SELECT * FROM jobs"
        ).fetchall()

    conn.close()

    return render_template(
        "index.html",
        jobs=job_list,
        student=session["student"]
    )



# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        conn = get_db()

        student = conn.execute(
            "SELECT * FROM students WHERE email = ? ",
            (email,)
        ).fetchone()

        conn.close()

        if student and check_password_hash(student["password"],password):
            session["student"] = student["name"]
            session["student_email"] = student["email"]
            return redirect("/")

        return "Invalid email or password"

    return render_template("login.html")




# ---------------- REGISTER ----------------

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        # Hash the password before storing it
        hashed_password = generate_password_hash(password)

        conn = get_db()

        try:
            conn.execute(
                "INSERT INTO students (name, email, password) VALUES (?, ?, ?)",
                (name, email, hashed_password)
            )

            conn.commit()

        except sqlite3.IntegrityError:
            conn.close()
            return "Email already registered. Please use another email."

        conn.close()

        return redirect("/login")

    return render_template("register.html")

# ---------------- JOB DETAILS ----------------
@app.route("/job/<int:job_id>")
def job_details(job_id):

    if "student" not in session:
        return redirect("/login")

    conn = get_db()

    job = conn.execute(
        "SELECT * FROM jobs WHERE id = ?",
        (job_id,)
    ).fetchone()

    conn.close()

    if job is None:
        return "Job not found"

    return render_template(
        "job_details.html",
        job=job
    )


# ---------------- APPLY FOR JOB ----------------
@app.route("/apply/<int:job_id>", methods=["GET", "POST"])

def apply(job_id):

    if "student" not in session:
        return redirect("/login")

    conn = get_db()

    job = conn.execute(
        "SELECT * FROM jobs WHERE id = ?",
        (job_id,)
    ).fetchone()

    if job is None:
        conn.close()
        return "Job not found"

    if request.method == "POST":

        name = session["student"]
        email = session["student_email"]

        # Get uploaded resume
        resume = request.files.get("resume")

        # Check resume
        if resume is None or resume.filename == "":
            conn.close()
            return "Please upload your resume."

        # Allow only PDF files
        if not resume.filename.lower().endswith(".pdf"):
            conn.close()
            return "Only PDF resumes are allowed."

        # Create unique filename
        from werkzeug.utils import secure_filename
        import uuid

        filename = secure_filename(resume.filename)
        unique_filename = str(uuid.uuid4()) + "_" + filename

        # Save resume inside uploads folder
        upload_folder = os.path.join(
            app.root_path,
            "uploads"
        )

        os.makedirs(upload_folder, exist_ok=True)

        resume.save(
            os.path.join(
                upload_folder,
                unique_filename
            )
        )

        # Check if student already applied for this job
        existing_application = conn.execute(
            """
            SELECT * FROM applications
            WHERE email = ? AND job = ? AND company = ?
            """,
            (email, job["title"], job["company"])
        ).fetchone()

        if existing_application:
            conn.close()

            # Remove uploaded resume because application already exists
            os.remove(
                os.path.join(
                    upload_folder,
                    unique_filename
                )
            )

            return "You have already applied for this job."

        from datetime import datetime

        applied_at = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        conn.execute(
            """
            INSERT INTO applications
            (name, email, job, company, location, status, applied_at, resume)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                name,
                email,
                job["title"],
                job["company"],
                job["location"],
                "Applied",
                applied_at,
                unique_filename
            )
        )

        conn.commit()
        conn.close()

        return redirect("/applications")

    conn.close()

    return render_template(
        "apply.html",
        job=job
    )

# ---------------- VIEW MY APPLICATIONS ----------------

@app.route("/applications")
def view_applications():

    # Check student login
    if "student" not in session:
        return redirect("/login")

    conn = get_db()

    applications = conn.execute(
        "SELECT * FROM applications WHERE email = ?",
        (session["student_email"],)
    ).fetchall()

    conn.close()

    return render_template(
        "applications.html",
        applications=applications
    )

# ---------------- STUDENT DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():

    if "student" not in session:
        return redirect("/login")

    conn = get_db()

    # Get student's applications
    applications = conn.execute(
        """
        SELECT * FROM applications
        WHERE email = ?
        ORDER BY applied_at DESC
        """,
        (session["student_email"],)
    ).fetchall()

    # Total applications
    total_applications = conn.execute(
        """
        SELECT COUNT(*) FROM applications
        WHERE email = ?
        """,
        (session["student_email"],)
    ).fetchone()[0]

    # Shortlisted applications
    shortlisted = conn.execute(
        """
        SELECT COUNT(*) FROM applications
        WHERE email = ? AND status = ?
        """,
        (session["student_email"], "Shortlisted")
    ).fetchone()[0]

    # Rejected applications
    rejected = conn.execute(
        """
        SELECT COUNT(*) FROM applications
        WHERE email = ? AND status = ?
        """,
        (session["student_email"], "Rejected")
    ).fetchone()[0]

    conn.close()

    return render_template(
        "dashboard.html",
        student=session["student"],
        email=session["student_email"],
        applications=applications,
        total_applications=total_applications,
        shortlisted=shortlisted,
        rejected=rejected
    )


# ---------------- STUDENT PROFILE ----------------

@app.route("/profile")
def profile():

    # Check student login
    if "student" not in session:
        return redirect("/login")

    conn = get_db()

    # Get student's applications
    applications = conn.execute(
        "SELECT * FROM applications WHERE email = ?",
        (session["student_email"],)
    ).fetchall()

    # Calculate application statistics
    total_applications = len(applications)

    shortlisted = conn.execute(
        """
        SELECT COUNT(*) FROM applications
        WHERE email = ? AND status = ?
        """,
        (session["student_email"], "Shortlisted")
    ).fetchone()[0]

    rejected = conn.execute(
        """
        SELECT COUNT(*) FROM applications
        WHERE email = ? AND status = ?
        """,
        (session["student_email"], "Rejected")
    ).fetchone()[0]

    conn.close()

    return render_template(
        "profile.html",
        student=session["student"],
        email=session["student_email"],
        total_applications=total_applications,
        shortlisted=shortlisted,
        rejected=rejected
    )

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():

    # Remove login session
    session.pop("student", None)

    return redirect("/login")

# ------------------ ADMIN LOGIN -------------------

@app.route("/admin_login", methods=["GET", "POST"])
def admin_login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        # Admin credentials
        if email == ADMIN_EMAIL and password == ADMIN_PASSWORD:

            session["admin"] = True

            return redirect("/admin")

        return "Invalid admin email or password"

    return render_template("admin_login.html")

# ------------------ ADD JOB -------------------
@app.route("/add_job", methods=["GET", "POST"])
def add_job():

    if "admin" not in session:
        return redirect("/admin_login")

    if request.method == "POST":

        title = request.form["title"]
        company = request.form["company"]
        location = request.form["location"]
        description = request.form["description"]
        skills = request.form["skills"]
        eligibility = request.form["eligibility"]

        conn = get_db()

        conn.execute(
            """
            INSERT INTO jobs
            (title, company, location, description, skills, eligibility)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                title,
                company,
                location,
                description,
                skills,
                eligibility
            )
        )

        conn.commit()
        conn.close()

        return redirect("/admin")

    return render_template("add_job.html")

# ------------------ EDIT JOB -------------------
@app.route("/edit_job/<int:job_id>", methods=["GET", "POST"])
def edit_job(job_id):

    if "admin" not in session:
        return redirect("/admin_login")

    conn = get_db()

    job = conn.execute(
        "SELECT * FROM jobs WHERE id = ?",
        (job_id,)
    ).fetchone()

    if job is None:
        conn.close()
        return "Job not found"

    if request.method == "POST":

        title = request.form["title"]
        company = request.form["company"]
        location = request.form["location"]
        description = request.form["description"]
        skills = request.form["skills"]
        eligibility = request.form["eligibility"]

        conn.execute(
            """
            UPDATE jobs
            SET title = ?,
                company = ?,
                location = ?,
                description = ?,
                skills = ?,
                eligibility = ?
            WHERE id = ?
            """,
            (
                title,
                company,
                location,
                description,
                skills,
                eligibility,
                job_id
            )
        )

        conn.commit()
        conn.close()

        return redirect("/admin")

    conn.close()

    return render_template(
        "edit_job.html",
        job=job
    )

# ------------------ DELETE JOB -------------------

@app.route("/delete_job/<int:job_id>")
def delete_job(job_id):

    # Check admin login
    if "admin" not in session:
        return redirect("/admin_login")

    conn = get_db()

    conn.execute(
        "DELETE FROM jobs WHERE id = ?",
        (job_id,)
    )

    conn.commit()
    conn.close()

    return redirect("/admin")

# ------------------ ADMIN DASHBOARD -------------------

@app.route("/admin")
def admin():

    # Check admin login
    if "admin" not in session:
        return redirect("/admin_login")

    conn = get_db()
    # Search applications
    search = request.args.get("search", "").strip().lower()
    status_filter = request.args.get("status", "All")

    query = """
        SELECT * FROM applications
        WHERE (
            LOWER(name) LIKE ?
            OR LOWER(email) LIKE ?
            OR LOWER(job) LIKE ?
            OR LOWER(company) LIKE ?
        )
    """

    params = [
        "%" + search + "%",
        "%" + search + "%",
        "%" + search + "%",
        "%" + search + "%"
    ]

    if status_filter != "All":
        query += " AND status = ?"
        params.append(status_filter)

    applications = conn.execute(
        query,
        params
    ).fetchall()

    # Get all jobs
    jobs = conn.execute(
        "SELECT * FROM jobs"
    ).fetchall()

    # Get all registered students
    students = conn.execute(
        "SELECT id, name, email FROM students"
    ).fetchall()

    # Dashboard statistics
    total_jobs = conn.execute(
        "SELECT COUNT(*) FROM jobs"
    ).fetchone()[0]

    total_applications = conn.execute(
        "SELECT COUNT(*) FROM applications"
    ).fetchone()[0]

    shortlisted = conn.execute(
        "SELECT COUNT(*) FROM applications WHERE status = ?",
        ("Shortlisted",)
    ).fetchone()[0]

    rejected = conn.execute(
        "SELECT COUNT(*) FROM applications WHERE status = ?",
        ("Rejected",)
    ).fetchone()[0]

    conn.close()

    return render_template(
        "admin.html",
        applications=applications,
        jobs=jobs,
        students=students,
        total_jobs=total_jobs,
        total_applications=total_applications,
        shortlisted=shortlisted,
        rejected=rejected
    )

# ---------------- VIEW RESUME ----------------
@app.route("/resume/<filename>")
def view_resume(filename):

    if "admin" not in session:
        return redirect("/admin_login")

    from flask import send_from_directory
    from werkzeug.utils import secure_filename

    safe_filename = secure_filename(filename)

    upload_folder = os.path.join(
        app.root_path,
        "uploads"
    )

    return send_from_directory(
        upload_folder,
        safe_filename
    )

# ---------------- ADMIN LOGOUT ----------------
@app.route("/admin_logout")
def admin_logout():

    session.pop("admin", None)

    return redirect("/admin_login")


# ---------------- STATUS UPDATE ----------------

@app.route("/update_status/<int:application_id>", methods=["POST"])
def update_status(application_id):

    if "admin" not in session:
        return redirect("/admin_login")

    new_status = request.form["status"]

    conn = get_db()

    conn.execute(
        "UPDATE applications SET status = ? WHERE id = ?",
        (new_status, application_id)
    )

    conn.commit()
    conn.close()

    return redirect("/admin")




# ---------------- RUN APPLICATION ----------------
if __name__ == "__main__":
    init_db()
    app.run(debug=True)