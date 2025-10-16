from flask import Flask, render_template, request, redirect, url_for, flash, Blueprint
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = "your_secret_key_here"

# ------------------------
# Database Setup
# ------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "students.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Students table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_number TEXT NOT NULL UNIQUE,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            course TEXT NOT NULL,
            year INTEGER NOT NULL
        )
    ''')
    # Courses table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        )
    ''')
    # Enrollments table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS enrollments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            course_id INTEGER NOT NULL,
            FOREIGN KEY(student_id) REFERENCES students(id),
            FOREIGN KEY(course_id) REFERENCES courses(id)
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# ------------------------
# Helper function for DB
# ------------------------
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# ------------------------
# STUDENT ROUTES
# ------------------------
@app.route("/")
def index():
    current_year = datetime.now().year
    return render_template("index.html", year=current_year)

@app.route("/add", methods=["GET", "POST"])
def add_student():
    if request.method == "POST":
        student_number = request.form.get('student_number', '').strip()
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        course = request.form.get('course', '').strip()
        year = request.form.get('year', '').strip()

        if not (student_number and first_name and last_name and course and year):
            flash("Please fill in all fields.", "danger")
            return redirect(url_for("add_student"))

        try:
            year_int = int(year)
        except ValueError:
            flash("Year must be a number.", "danger")
            return redirect(url_for("add_student"))

        conn = get_db_connection()
        try:
            conn.execute(
                "INSERT INTO students (student_number, first_name, last_name, course, year) VALUES (?, ?, ?, ?, ?)",
                (student_number, first_name, last_name, course, year_int)
            )
            conn.commit()
            flash("Student added successfully!", "success")
        except sqlite3.IntegrityError:
            flash("Student number already exists.", "danger")
        finally:
            conn.close()
        return redirect(url_for("view_students"))
    return render_template("add_student.html")

@app.route("/view")
def view_students():
    conn = get_db_connection()
    students = conn.execute("SELECT * FROM students ORDER BY id DESC").fetchall()
    conn.close()
    return render_template("view_students.html", students=students)

@app.route("/edit/<int:student_id>", methods=["GET", "POST"])
def edit_student(student_id):
    conn = get_db_connection()
    student = conn.execute("SELECT * FROM students WHERE id=?", (student_id,)).fetchone()
    if not student:
        flash("Student not found.", "danger")
        return redirect(url_for("view_students"))

    if request.method == "POST":
        student_number = request.form.get('student_number', '').strip()
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        course = request.form.get('course', '').strip()
        year = request.form.get('year', '').strip()

        if not (student_number and first_name and last_name and course and year):
            flash("Please fill in all fields.", "danger")
            return redirect(url_for("edit_student", student_id=student_id))

        try:
            year_int = int(year)
        except ValueError:
            flash("Year must be a number.", "danger")
            return redirect(url_for("edit_student", student_id=student_id))

        try:
            conn.execute('''
                UPDATE students
                SET student_number=?, first_name=?, last_name=?, course=?, year=?
                WHERE id=?
            ''', (student_number, first_name, last_name, course, year_int, student_id))
            conn.commit()
            flash("Student updated successfully!", "success")
        except sqlite3.IntegrityError:
            flash("Student number already exists.", "danger")
        finally:
            conn.close()

        return redirect(url_for("view_students"))

    conn.close()
    return render_template("edit_student.html", student=student)

@app.route("/delete/<int:student_id>", methods=["GET", "POST"])
def delete_student(student_id):
    conn = get_db_connection()
    student = conn.execute("SELECT * FROM students WHERE id=?", (student_id,)).fetchone()
    if not student:
        flash("Student not found.", "danger")
        return redirect(url_for("view_students"))

    if request.method == "POST":
        conn.execute("DELETE FROM students WHERE id=?", (student_id,))
        conn.commit()
        conn.close()
        flash("Student deleted successfully!", "info")
        return redirect(url_for("view_students"))

    conn.close()
    return render_template("delete_student.html", student=student)

@app.route("/search", methods=["GET", "POST"])
def search_students():
    students = []
    query = ""
    if request.method == "POST":
        query = request.form['query'].strip()
        conn = get_db_connection()
        students = conn.execute('''
            SELECT * FROM students
            WHERE student_number LIKE ?
            OR first_name LIKE ?
            OR last_name LIKE ?
            OR course LIKE ?
        ''', (f"%{query}%", f"%{query}%", f"%{query}%", f"%{query}%")).fetchall()
        conn.close()
        if not students:
            flash("No matching students found.", "info")
    return render_template("search_students.html", students=students, query=query)

# ------------------------
# COURSES BLUEPRINT
# ------------------------
courses_bp = Blueprint('courses', __name__, template_folder='templates')

@courses_bp.route("/courses")
def view_courses():
    conn = get_db_connection()
    courses = conn.execute("SELECT * FROM courses ORDER BY id DESC").fetchall()
    conn.close()
    return render_template("view_courses.html", courses=courses)

@courses_bp.route("/courses/add", methods=["GET", "POST"])
def add_course():
    if request.method == "POST":
        name = request.form.get("name").strip()
        if name:
            conn = get_db_connection()
            try:
                conn.execute("INSERT INTO courses (name) VALUES (?)", (name,))
                conn.commit()
                flash("Course added successfully!", "success")
            except sqlite3.IntegrityError:
                flash("Course name already exists.", "danger")
            finally:
                conn.close()
            return redirect(url_for("courses.view_courses"))
    return render_template("add_course.html")

@courses_bp.route("/courses/edit/<int:course_id>", methods=["GET", "POST"])
def edit_course(course_id):
    conn = get_db_connection()
    course = conn.execute("SELECT * FROM courses WHERE id=?", (course_id,)).fetchone()
    if not course:
        flash("Course not found.", "danger")
        return redirect(url_for("courses.view_courses"))

    if request.method == "POST":
        new_name = request.form.get("name").strip()
        if new_name:
            try:
                conn.execute("UPDATE courses SET name=? WHERE id=?", (new_name, course_id))
                conn.commit()
                flash("Course updated successfully!", "success")
            except sqlite3.IntegrityError:
                flash("Course name already exists.", "danger")
            finally:
                conn.close()
            return redirect(url_for("courses.view_courses"))

    conn.close()
    return render_template("edit_course.html", course=course)

@courses_bp.route("/courses/delete/<int:course_id>", methods=["GET", "POST"])
def delete_course(course_id):
    conn = get_db_connection()
    course = conn.execute("SELECT * FROM courses WHERE id=?", (course_id,)).fetchone()
    if not course:
        flash("Course not found.", "danger")
        return redirect(url_for("courses.view_courses"))

    if request.method == "POST":
        conn.execute("DELETE FROM courses WHERE id=?", (course_id,))
        conn.commit()
        conn.close()
        flash("Course deleted successfully!", "info")
        return redirect(url_for("courses.view_courses"))

    conn.close()
    return render_template("delete_course.html", course=course)

# ------------------------
# ENROLLMENTS BLUEPRINT
# ------------------------
enroll_bp = Blueprint('enrollments', __name__, template_folder='templates')

@enroll_bp.route("/enrollments")
def view_enrollments():
    conn = get_db_connection()
    enrollments = conn.execute('''
        SELECT e.id, s.student_number, s.first_name, s.last_name, c.name as course_name
        FROM enrollments e
        JOIN students s ON e.student_id = s.id
        JOIN courses c ON e.course_id = c.id
        ORDER BY e.id DESC
    ''').fetchall()
    conn.close()
    return render_template("view_enrollments.html", enrollments=enrollments)

@enroll_bp.route("/enrollments/add", methods=["GET", "POST"])
def add_enrollment():
    conn = get_db_connection()
    students = conn.execute("SELECT * FROM students").fetchall()
    courses = conn.execute("SELECT * FROM courses").fetchall()

    if request.method == "POST":
        student_id = request.form.get("student_id")
        course_id = request.form.get("course_id")
        if student_id and course_id:
            conn.execute("INSERT INTO enrollments (student_id, course_id) VALUES (?, ?)",
                         (student_id, course_id))
            conn.commit()
            conn.close()
            flash("Enrollment added successfully!", "success")
            return redirect(url_for("enrollments.view_enrollments"))

    conn.close()
    return render_template("add_enrollment.html", students=students, courses=courses)

# ------------------------
# REGISTER BLUEPRINTS
# ------------------------
app.register_blueprint(courses_bp)
app.register_blueprint(enroll_bp)

# ------------------------
# RUN APP
# ------------------------
if __name__ == "__main__":
    app.run(debug=True)
