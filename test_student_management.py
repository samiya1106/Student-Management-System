"""
Automated tests for student_management.py (uses Python's built-in unittest).

Every test uses a temporary database file that is deleted afterwards,
so the real database in the data folder is never read or changed.
No manual input is needed (the menu tests use fake input).
"""

import io
import os
import shutil
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

import student_management as sm


class BaseTest(unittest.TestCase):
    """Creates a fresh temporary database for every test."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_students.db")

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def add_sample(self, roll="CS101", name="Test Student",
                   course="Computer Engineering", marks=80):
        sm.add_student(roll, name, course, marks, self.db_path)


class TestDatabaseSafety(BaseTest):
    def test_temp_database_is_not_real_database(self):
        self.assertNotEqual(
            os.path.abspath(self.db_path), os.path.abspath(sm.DEFAULT_DB_PATH)
        )

    def test_new_database_is_empty(self):
        self.assertEqual(sm.get_all_students(self.db_path), [])


class TestAddStudent(BaseTest):
    def test_add_student_success(self):
        self.add_sample()
        student = sm.get_student("CS101", self.db_path)
        self.assertEqual(student["name"], "Test Student")
        self.assertEqual(student["course"], "Computer Engineering")
        self.assertEqual(student["marks"], 80.0)

    def test_roll_number_is_trimmed_and_uppercase(self):
        self.add_sample(roll="  cs102  ")
        self.assertIsNotNone(sm.get_student("CS102", self.db_path))

    def test_duplicate_roll_number_rejected(self):
        self.add_sample()
        with self.assertRaises(ValueError):
            self.add_sample(name="Another Student")
        self.assertEqual(len(sm.get_all_students(self.db_path)), 1)

    def test_duplicate_roll_number_is_case_insensitive(self):
        self.add_sample(roll="CS101")
        with self.assertRaises(ValueError):
            self.add_sample(roll="cs101")

    def test_invalid_roll_numbers(self):
        for bad in ["", "   ", "AB CD", "AB@1", "A" * 21, None]:
            with self.subTest(roll=bad):
                with self.assertRaises(ValueError):
                    self.add_sample(roll=bad)

    def test_invalid_names(self):
        for bad in ["", "123", "John@", "A" * 51, None]:
            with self.subTest(name=bad):
                with self.assertRaises(ValueError):
                    self.add_sample(name=bad)

    def test_empty_course_rejected(self):
        for bad in ["", "   ", None]:
            with self.subTest(course=bad):
                with self.assertRaises(ValueError):
                    self.add_sample(course=bad)

    def test_invalid_marks(self):
        for bad in ["abc", "", -1, 101, "100.5", "nan", None]:
            with self.subTest(marks=bad):
                with self.assertRaises(ValueError):
                    self.add_sample(marks=bad)

    def test_marks_boundaries_are_accepted(self):
        self.add_sample(roll="LOW1", marks=0)
        self.add_sample(roll="HIGH1", marks=100)
        self.assertEqual(sm.get_student("LOW1", self.db_path)["marks"], 0.0)
        self.assertEqual(sm.get_student("HIGH1", self.db_path)["marks"], 100.0)

    def test_invalid_add_does_not_save_anything(self):
        with self.assertRaises(ValueError):
            self.add_sample(marks="abc")
        self.assertEqual(sm.get_all_students(self.db_path), [])


class TestViewAndSearch(BaseTest):
    def test_view_all_students_sorted_by_roll(self):
        self.add_sample(roll="CS102", name="Student Two")
        self.add_sample(roll="CS101", name="Student One")
        students = sm.get_all_students(self.db_path)
        self.assertEqual([s["roll_number"] for s in students], ["CS101", "CS102"])

    def test_search_existing_student(self):
        self.add_sample()
        self.assertEqual(sm.get_student("cs101", self.db_path)["roll_number"], "CS101")

    def test_search_missing_student_returns_none(self):
        self.assertIsNone(sm.get_student("NOPE1", self.db_path))


class TestUpdateStudent(BaseTest):
    def test_update_all_fields(self):
        self.add_sample()
        sm.update_student("CS101", "New Name", "Mechanical", 95, self.db_path)
        student = sm.get_student("CS101", self.db_path)
        self.assertEqual(student["name"], "New Name")
        self.assertEqual(student["course"], "Mechanical")
        self.assertEqual(student["marks"], 95.0)

    def test_update_only_marks_keeps_other_fields(self):
        self.add_sample()
        sm.update_student("CS101", marks=55, db_path=self.db_path)
        student = sm.get_student("CS101", self.db_path)
        self.assertEqual(student["name"], "Test Student")
        self.assertEqual(student["marks"], 55.0)

    def test_update_missing_student(self):
        with self.assertRaises(ValueError):
            sm.update_student("NOPE1", marks=50, db_path=self.db_path)

    def test_update_with_invalid_marks_keeps_old_value(self):
        self.add_sample()
        with self.assertRaises(ValueError):
            sm.update_student("CS101", marks=500, db_path=self.db_path)
        self.assertEqual(sm.get_student("CS101", self.db_path)["marks"], 80.0)

    def test_update_with_no_values_rejected(self):
        self.add_sample()
        with self.assertRaises(ValueError):
            sm.update_student("CS101", db_path=self.db_path)


class TestDeleteStudent(BaseTest):
    def test_delete_existing_student(self):
        self.add_sample()
        sm.delete_student("CS101", self.db_path)
        self.assertIsNone(sm.get_student("CS101", self.db_path))

    def test_delete_missing_student(self):
        with self.assertRaises(ValueError):
            sm.delete_student("NOPE1", self.db_path)

    def test_delete_removes_only_the_target(self):
        self.add_sample(roll="CS101")
        self.add_sample(roll="CS102", name="Student Two")
        sm.delete_student("CS101", self.db_path)
        remaining = sm.get_all_students(self.db_path)
        self.assertEqual([s["roll_number"] for s in remaining], ["CS102"])


class TestMenu(BaseTest):
    """Run the menu with fake keyboard input (no manual typing needed)."""

    def run_menu(self, inputs):
        output = io.StringIO()
        with patch("builtins.input", side_effect=inputs), redirect_stdout(output):
            sm.main(self.db_path)
        return output.getvalue()

    def test_menu_add_then_view(self):
        text = self.run_menu([
            "1", "CS101", "Test Student", "Computer Engineering", "85",
            "2",
            "6",
        ])
        self.assertIn("Student added successfully", text)
        self.assertIn("Test Student", text)
        self.assertEqual(len(sm.get_all_students(self.db_path)), 1)

    def test_menu_invalid_choice(self):
        text = self.run_menu(["9", "6"])
        self.assertIn("Invalid choice", text)

    def test_menu_duplicate_roll_shows_error(self):
        text = self.run_menu([
            "1", "CS101", "First Student", "Course A", "50",
            "1", "cs101", "Second Student", "Course B", "60",
            "6",
        ])
        self.assertIn("already exists", text)
        self.assertEqual(len(sm.get_all_students(self.db_path)), 1)


if __name__ == "__main__":
    unittest.main()
