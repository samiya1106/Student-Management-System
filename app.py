"""
Student Management System - Website (Flask)
-------------------------------------------
This file turns the terminal application into a website.
It does NOT repeat any database code: every action calls a function
from student_management.py (the same file the terminal menu uses).

Run it with:   python app.py
Then open:     http://127.0.0.1:5000
"""

import hmac
import os
import secrets

from flask import (
    Flask, abort, flash, redirect, render_template, request, session, url_for,
)

import student_management as sm


def create_app(db_path=None):
    """
    Build the Flask website.
    db_path lets the tests use a temporary database. When it is None,
    the real database (data/students.db) is used.
    """
    app = Flask(__name__)
    # The secret key signs the session cookie (used for flash messages and CSRF).
    # For real use, set your own: export SECRET_KEY="a-long-random-text"
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-me")
    app.config["DB_PATH"] = db_path

    sm.init_db(db_path)  # make sure the database and table exist

    # ------------------------------------------------------------------
    # Simple CSRF protection: every form carries a secret token, and every
    # POST request is rejected unless the token matches the one in the session.
    # ------------------------------------------------------------------
    def get_csrf_token():
        if "_csrf" not in session:
            session["_csrf"] = secrets.token_hex(16)
        return session["_csrf"]

    app.jinja_env.globals["csrf_token"] = get_csrf_token

    @app.before_request
    def check_csrf_token():
        if request.method == "POST":
            sent = request.form.get("csrf_token", "")
            expected = session.get("_csrf", "")
            if not expected or not hmac.compare_digest(sent, expected):
                abort(400)

    def db():
        """Return the database path used by this website."""
        return app.config["DB_PATH"]

    # ------------------------------------------------------------------
    # Pages
    # ------------------------------------------------------------------
    @app.route("/")
    def dashboard():
        students = sm.get_all_students(db())
        total = len(students)
        marks = [s["marks"] for s in students]
        stats = {
            "total": total,
            "average": (sum(marks) / total) if total else 0,
            "highest": max(marks) if total else 0,
            "courses": len({s["course"].lower() for s in students}),
        }
        return render_template(
            "index.html", students=students, stats=stats, page="dashboard"
        )

    @app.route("/students")
    def students_page():
        query = request.args.get("q", "").strip()
        students = sm.search_students(query, db())
        return render_template(
            "students.html", students=students, query=query, page="students"
        )

    @app.route("/add", methods=["GET", "POST"])
    def add_student_page():
        values = {"roll_number": "", "name": "", "course": "", "marks": ""}
        errors = {}
        if request.method == "POST":
            values = read_form()
            errors = check_form(values, include_roll=True)
            if not errors:
                try:
                    sm.add_student(
                        values["roll_number"], values["name"],
                        values["course"], values["marks"], db(),
                    )
                except ValueError as error:  # for example: duplicate roll number
                    errors["roll_number"] = str(error)
                else:
                    flash("Student added successfully.", "success")
                    return redirect(url_for("students_page"))
            flash("Please correct the errors in the form.", "error")
        return render_template(
            "form.html", mode="add", values=values, errors=errors, page="add"
        )

    @app.route("/edit/<roll_number>", methods=["GET", "POST"])
    def edit_student_page(roll_number):
        try:
            student = sm.get_student(roll_number, db())
        except ValueError:
            student = None
        if student is None:
            flash("Student not found.", "error")
            return redirect(url_for("students_page"))

        values = dict(student)
        values["marks"] = f"{student['marks']:g}"  # 80.0 is shown as 80
        errors = {}
        if request.method == "POST":
            values = read_form()
            values["roll_number"] = student["roll_number"]  # cannot be changed
            errors = check_form(values, include_roll=False)
            if not errors:
                try:
                    sm.update_student(
                        student["roll_number"], values["name"],
                        values["course"], values["marks"], db(),
                    )
                except ValueError as error:
                    flash(str(error), "error")
                else:
                    flash("Student updated successfully.", "success")
                    return redirect(url_for("students_page"))
            else:
                flash("Please correct the errors in the form.", "error")
        return render_template(
            "form.html", mode="edit", values=values, errors=errors, page="students"
        )

    @app.route("/delete/<roll_number>", methods=["GET", "POST"])
    def delete_student_page(roll_number):
        try:
            student = sm.get_student(roll_number, db())
        except ValueError:
            student = None
        if student is None:
            flash("Student not found.", "error")
            return redirect(url_for("students_page"))

        if request.method == "POST":
            try:
                sm.delete_student(student["roll_number"], db())
            except ValueError as error:
                flash(str(error), "error")
            else:
                flash(f"Student {student['roll_number']} deleted successfully.", "success")
            return redirect(url_for("students_page"))
        # GET: show the "Are you sure?" confirmation page
        return render_template("confirm_delete.html", student=student, page="students")

    # ------------------------------------------------------------------
    # Helpers for the forms
    # ------------------------------------------------------------------
    def read_form():
        """Read the four form fields (as text) from the submitted form."""
        return {
            "roll_number": request.form.get("roll_number", "").strip(),
            "name": request.form.get("name", "").strip(),
            "course": request.form.get("course", "").strip(),
            "marks": request.form.get("marks", "").strip(),
        }

    def check_form(values, include_roll):
        """Validate each field with the functions from student_management.py."""
        checks = [
            ("name", sm.validate_name),
            ("course", sm.validate_course),
            ("marks", sm.validate_marks),
        ]
        if include_roll:
            checks.insert(0, ("roll_number", sm.validate_roll_number))
        errors = {}
        for field, validate in checks:
            try:
                validate(values[field])
            except ValueError as error:
                errors[field] = str(error)
        return errors

    # ------------------------------------------------------------------
    # Error pages
    # ------------------------------------------------------------------
    @app.errorhandler(404)
    def not_found(error):
        return render_template(
            "error.html", code=404, title="Page not found",
            message="The page you are looking for does not exist.", page=""
        ), 404

    @app.errorhandler(400)
    def bad_request(error):
        return render_template(
            "error.html", code=400, title="Form expired",
            message="Your form could not be verified (the page may have been "
                    "open for too long). Please go back, refresh the page and try again.",
            page=""
        ), 400

    return app


if __name__ == "__main__":
    # Set FLASK_DEBUG=1 to see detailed errors while developing.
    create_app().run(
        host="127.0.0.1", port=5000, debug=os.environ.get("FLASK_DEBUG") == "1"
    )
