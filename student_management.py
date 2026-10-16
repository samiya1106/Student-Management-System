"""
Student Management System
-------------------------
A simple menu-driven program to manage student records.
Records are stored permanently in an SQLite database.

The file has two parts:
1. Database functions (add, view, search, update, delete) - easy to test.
2. Menu functions (input and output) - talk to the user.
"""

import os
import re
import sqlite3

# Folder that contains this file. Used to build the default database path.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Default database file: <project folder>/data/students.db
DEFAULT_DB_PATH = os.path.join(BASE_DIR, "data", "students.db")

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS students (
    roll_number TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    course      TEXT NOT NULL,
    marks       REAL NOT NULL CHECK (marks >= 0 AND marks <= 100)
)
"""


# ---------------------------------------------------------------------------
# Part 1: Database functions
# Every function accepts an optional db_path. Tests pass a temporary file here,
# so the real database in the data folder is never touched by tests.
# ---------------------------------------------------------------------------

def get_connection(db_path=None):
    """Open the database (creating the folder and table if needed)."""
    path = db_path or DEFAULT_DB_PATH
    folder = os.path.dirname(path)
    if folder:
        os.makedirs(folder, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.execute(CREATE_TABLE_SQL)
    connection.commit()
    return connection


def init_db(db_path=None):
    """Make sure the database file and the students table exist."""
    get_connection(db_path).close()


def _run(sql, params=(), db_path=None, fetch=False):
    """Run one SQL statement, save changes, and always close the connection."""
    connection = get_connection(db_path)
    try:
        with connection:  # commits on success, rolls back on error
            cursor = connection.execute(sql, params)
            if fetch:
                return cursor.fetchall()
            return cursor.rowcount
    finally:
        connection.close()


def _clean_text(value):
    """Turn a value into a stripped string (None becomes an empty string)."""
    return "" if value is None else str(value).strip()


def _row_to_dict(row):
    """Convert a database row (tuple) into a dictionary."""
    return {
        "roll_number": row[0],
        "name": row[1],
        "course": row[2],
        "marks": row[3],
    }


# ----- Input validation -----

def validate_roll_number(value):
    """Roll number: 1-20 letters, digits or hyphens. Stored in UPPERCASE."""
    roll = _clean_text(value).upper()
    if not re.fullmatch(r"[A-Z0-9-]{1,20}", roll):
        raise ValueError(
            "Roll number must be 1-20 characters (letters, digits or '-')."
        )
    return roll


def validate_name(value):
    """Name: starts with a letter; letters, spaces, . ' - allowed; max 50."""
    name = _clean_text(value)
    if not name or len(name) > 50 or not re.fullmatch(r"[A-Za-z][A-Za-z .'-]*", name):
        raise ValueError(
            "Name must start with a letter, use only letters, spaces, "
            ". ' - and be at most 50 characters."
        )
    return name


def validate_course(value):
    """Course: not empty, at most 50 characters."""
    course = _clean_text(value)
    if not course or len(course) > 50:
        raise ValueError("Course must not be empty and must be at most 50 characters.")
    return course


def validate_marks(value):
    """Marks: a number from 0 to 100."""
    try:
        marks = float(_clean_text(value))
    except ValueError:
        raise ValueError("Marks must be a number.") from None
    if not 0 <= marks <= 100:  # also rejects NaN
        raise ValueError("Marks must be between 0 and 100.")
    return marks


# ----- Main operations -----

def add_student(roll_number, name, course, marks, db_path=None):
    """Add a new student. Raises ValueError for bad input or duplicate roll."""
    roll = validate_roll_number(roll_number)
    name = validate_name(name)
    course = validate_course(course)
    marks = validate_marks(marks)
    try:
        _run(
            "INSERT INTO students (roll_number, name, course, marks) "
            "VALUES (?, ?, ?, ?)",
            (roll, name, course, marks),
            db_path,
        )
    except sqlite3.IntegrityError:
        raise ValueError(f"Roll number {roll} already exists.") from None


def get_all_students(db_path=None):
    """Return a list of all students (sorted by roll number)."""
    rows = _run(
        "SELECT roll_number, name, course, marks FROM students "
        "ORDER BY roll_number",
        (),
        db_path,
        fetch=True,
    )
    return [_row_to_dict(row) for row in rows]


def search_students(term, db_path=None):
    """
    Find students whose roll number, name or course contains the given text.
    The search ignores upper/lower case. An empty search returns everyone.
    """
    term = _clean_text(term)
    if not term:
        return get_all_students(db_path)
    # Treat %, _ and \ as normal characters (not as SQL wildcards).
    escaped = term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    pattern = f"%{escaped}%"
    rows = _run(
        "SELECT roll_number, name, course, marks FROM students "
        "WHERE roll_number LIKE ? ESCAPE '\\' "
        "OR name LIKE ? ESCAPE '\\' "
        "OR course LIKE ? ESCAPE '\\' "
        "ORDER BY roll_number",
        (pattern, pattern, pattern),
        db_path,
        fetch=True,
    )
    return [_row_to_dict(row) for row in rows]


def get_student(roll_number, db_path=None):
    """Return one student as a dictionary, or None if not found."""
    roll = validate_roll_number(roll_number)
    rows = _run(
        "SELECT roll_number, name, course, marks FROM students "
        "WHERE roll_number = ?",
        (roll,),
        db_path,
        fetch=True,
    )
    return _row_to_dict(rows[0]) if rows else None


def update_student(roll_number, name=None, course=None, marks=None, db_path=None):
    """
    Update the given fields of a student. Fields left as None are unchanged.
    Raises ValueError if input is invalid or the student does not exist.
    """
    roll = validate_roll_number(roll_number)

    # Collect only the fields that were provided (and validate them).
    changes = {}
    if name is not None:
        changes["name"] = validate_name(name)
    if course is not None:
        changes["course"] = validate_course(course)
    if marks is not None:
        changes["marks"] = validate_marks(marks)

    if not changes:
        raise ValueError("Nothing to update. Please provide at least one new value.")
    if get_student(roll, db_path) is None:
        raise ValueError(f"No student found with roll number {roll}.")

    # Column names come from the code above (never from the user), so this is safe.
    set_clause = ", ".join(f"{column} = ?" for column in changes)
    _run(
        f"UPDATE students SET {set_clause} WHERE roll_number = ?",
        tuple(changes.values()) + (roll,),
        db_path,
    )


def delete_student(roll_number, db_path=None):
    """Delete a student. Raises ValueError if the student does not exist."""
    roll = validate_roll_number(roll_number)
    deleted_rows = _run("DELETE FROM students WHERE roll_number = ?", (roll,), db_path)
    if deleted_rows == 0:
        raise ValueError(f"No student found with roll number {roll}.")


# ---------------------------------------------------------------------------
# Part 2: Menu (command-line interface)
# ---------------------------------------------------------------------------

def print_students(students):
    """Print a list of students as a simple table."""
    if not students:
        print("No student records found.")
        return
    print(f"{'Roll No':<12}{'Name':<25}{'Course':<25}{'Marks':>7}")
    print("-" * 69)
    for s in students:
        print(
            f"{s['roll_number']:<12}{s['name']:<25}{s['course']:<25}{s['marks']:>7.2f}"
        )


def print_menu():
    print()
    print("===== Student Management System =====")
    print("1. Add student")
    print("2. View all students")
    print("3. Search student by roll number")
    print("4. Update student")
    print("5. Delete student")
    print("6. Exit")


def menu_add_student(db_path=None):
    roll = input("Enter roll number: ")
    name = input("Enter name: ")
    course = input("Enter course: ")
    marks = input("Enter marks (0-100): ")
    add_student(roll, name, course, marks, db_path)
    print("Success: Student added successfully.")


def menu_view_students(db_path=None):
    print_students(get_all_students(db_path))


def menu_search_student(db_path=None):
    roll = input("Enter roll number to search: ")
    student = get_student(roll, db_path)
    if student is None:
        print(f"Error: No student found with roll number {roll.strip().upper()}.")
    else:
        print_students([student])


def menu_update_student(db_path=None):
    roll = input("Enter roll number to update: ")
    student = get_student(roll, db_path)
    if student is None:
        print(f"Error: No student found with roll number {roll.strip().upper()}.")
        return
    print("Press Enter without typing to keep the current value.")
    new_name = input(f"New name [{student['name']}]: ").strip()
    new_course = input(f"New course [{student['course']}]: ").strip()
    new_marks = input(f"New marks [{student['marks']:.2f}]: ").strip()
    update_student(
        student["roll_number"],
        new_name or None,
        new_course or None,
        new_marks or None,
        db_path,
    )
    print("Success: Student updated successfully.")


def menu_delete_student(db_path=None):
    roll = input("Enter roll number to delete: ")
    confirm = input("Are you sure you want to delete this student? (y/n): ")
    if confirm.strip().lower() != "y":
        print("Delete cancelled.")
        return
    delete_student(roll, db_path)
    print("Success: Student deleted successfully.")


def main(db_path=None):
    """Run the menu loop until the user chooses Exit."""
    init_db(db_path)
    actions = {
        "1": menu_add_student,
        "2": menu_view_students,
        "3": menu_search_student,
        "4": menu_update_student,
        "5": menu_delete_student,
    }
    while True:
        print_menu()
        choice = input("Enter your choice (1-6): ").strip()
        if choice == "6":
            print("Goodbye!")
            break
        action = actions.get(choice)
        if action is None:
            print("Error: Invalid choice. Please enter a number from 1 to 6.")
            continue
        try:
            action(db_path)
        except ValueError as error:
            print(f"Error: {error}")
        except sqlite3.Error as error:
            print(f"Database error: {error}")


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\nProgram closed.")
