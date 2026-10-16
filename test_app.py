"""
Automated tests for the website (app.py) and the new search function.

Like the other tests, these use a temporary database that is deleted afterwards.
The real database in the data folder is never used. No browser is needed:
Flask's built-in test client sends fake requests to the website.
"""

import os
import shutil
import tempfile
import unittest

import student_management as sm

try:
    from app import create_app
except ImportError:  # Flask is not installed
    create_app = None


class TempDbTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_web.db")

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)


class TestSearchFunction(TempDbTest):
    """Tests for search_students() (does not need Flask)."""

    def setUp(self):
        super().setUp()
        sm.add_student("CS101", "Asha Verma", "Computer Engineering", 90, self.db_path)
        sm.add_student("ME201", "Ravi Kumar", "Mechanical", 70, self.db_path)
        sm.add_student("CS102", "Neha Rao", "Computer Engineering", 55, self.db_path)

    def rolls(self, term):
        return [s["roll_number"] for s in sm.search_students(term, self.db_path)]

    def test_search_by_roll_number(self):
        self.assertEqual(self.rolls("me2"), ["ME201"])

    def test_search_by_name_ignores_case(self):
        self.assertEqual(self.rolls("RAVI"), ["ME201"])

    def test_search_by_course(self):
        self.assertEqual(self.rolls("computer"), ["CS101", "CS102"])

    def test_empty_search_returns_everyone(self):
        self.assertEqual(len(self.rolls("")), 3)
        self.assertEqual(len(self.rolls("   ")), 3)

    def test_no_match_returns_empty_list(self):
        self.assertEqual(self.rolls("zzz"), [])

    def test_wildcard_characters_are_plain_text(self):
        self.assertEqual(self.rolls("%"), [])
        self.assertEqual(self.rolls("_"), [])

    def test_sql_injection_text_is_harmless(self):
        self.assertEqual(self.rolls("' OR '1'='1"), [])
        self.assertEqual(len(sm.get_all_students(self.db_path)), 3)


@unittest.skipIf(create_app is None, "Flask is not installed")
class TestWebsite(TempDbTest):
    """Tests for every page and action of the website."""

    def setUp(self):
        super().setUp()
        self.app = create_app(self.db_path)
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        # Give the test client a CSRF token (a real browser gets it from the form).
        with self.client.session_transaction() as session:
            session["_csrf"] = "test-token"

    def post(self, url, data=None, follow=True):
        data = dict(data or {})
        data["csrf_token"] = "test-token"
        return self.client.post(url, data=data, follow_redirects=follow)

    def add(self, roll="CS101", name="Test Student", course="Computer Engineering", marks="80"):
        return self.post("/add", {
            "roll_number": roll, "name": name, "course": course, "marks": marks,
        })

    # ----- viewing pages -----

    def test_all_pages_load(self):
        for url in ["/", "/students", "/add"]:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)

    def test_unknown_page_shows_404(self):
        response = self.client.get("/no-such-page")
        self.assertEqual(response.status_code, 404)
        self.assertIn(b"Page not found", response.data)

    def test_dashboard_shows_total_and_students(self):
        self.assertIn(b"No student records found", self.client.get("/").data)
        self.add()
        self.add(roll="CS102", name="Second Student", marks="60")
        page = self.client.get("/").data.decode()
        self.assertIn("Total Students", page)
        self.assertIn("Test Student", page)
        self.assertIn("Second Student", page)
        self.assertIn("70.0", page)  # average of 80 and 60

    def test_navigation_links_are_present(self):
        page = self.client.get("/").data.decode()
        for link in ['href="/"', 'href="/students"', 'href="/add"']:
            self.assertIn(link, page)

    # ----- adding -----

    def test_add_student_success(self):
        response = self.add()
        self.assertIn(b"Student added successfully", response.data)
        self.assertIn(b"Test Student", response.data)
        self.assertEqual(sm.get_student("CS101", self.db_path)["marks"], 80.0)

    def test_add_with_empty_fields_shows_errors(self):
        response = self.add(roll="", name="", course="", marks="")
        page = response.data.decode()
        self.assertIn("Roll number must be", page)
        self.assertIn("Name must start with a letter", page)
        self.assertIn("Course must not be empty", page)
        self.assertIn("Marks must be a number", page)
        self.assertEqual(sm.get_all_students(self.db_path), [])

    def test_add_with_invalid_marks_keeps_typed_values(self):
        page = self.add(marks="150", name="Keep Me").data.decode()
        self.assertIn("Marks must be between 0 and 100", page)
        self.assertIn('value="Keep Me"', page)
        self.assertEqual(sm.get_all_students(self.db_path), [])

    def test_add_duplicate_roll_number_shows_error(self):
        self.add()
        page = self.add(name="Another Student").data.decode()
        self.assertIn("already exists", page)
        self.assertEqual(len(sm.get_all_students(self.db_path)), 1)

    # ----- searching -----

    def test_search_page_filters_results(self):
        self.add(roll="CS101", name="Asha Verma", course="Computer Engineering")
        self.add(roll="ME201", name="Ravi Kumar", course="Mechanical")
        page = self.client.get("/students?q=mech").data.decode()
        self.assertIn("Ravi Kumar", page)
        self.assertNotIn("Asha Verma", page)
        page = self.client.get("/students?q=asha").data.decode()
        self.assertIn("Asha Verma", page)
        self.assertNotIn("Ravi Kumar", page)
        self.assertIn("No student records found", self.client.get("/students?q=zzz").data.decode())

    def test_search_text_is_escaped_in_page(self):
        page = self.client.get("/students?q=<script>alert(1)</script>").data.decode()
        self.assertNotIn("<script>alert(1)</script>", page)

    # ----- editing -----

    def test_edit_page_shows_current_values(self):
        self.add()
        page = self.client.get("/edit/CS101").data.decode()
        self.assertIn('value="Test Student"', page)
        self.assertIn('value="80"', page)
        self.assertIn("readonly", page)

    def test_edit_student_success(self):
        self.add()
        response = self.post("/edit/CS101", {
            "name": "New Name", "course": "Mechanical", "marks": "95.5",
        })
        self.assertIn(b"Student updated successfully", response.data)
        student = sm.get_student("CS101", self.db_path)
        self.assertEqual(student["name"], "New Name")
        self.assertEqual(student["course"], "Mechanical")
        self.assertEqual(student["marks"], 95.5)

    def test_edit_cannot_change_roll_number(self):
        self.add()
        self.post("/edit/CS101", {
            "roll_number": "HACK1", "name": "Test Student",
            "course": "Computer Engineering", "marks": "80",
        })
        self.assertIsNotNone(sm.get_student("CS101", self.db_path))
        self.assertIsNone(sm.get_student("HACK1", self.db_path))

    def test_edit_with_invalid_data_shows_errors_and_keeps_old_data(self):
        self.add()
        page = self.post("/edit/CS101", {
            "name": "", "course": "Mechanical", "marks": "abc",
        }).data.decode()
        self.assertIn("Name must start with a letter", page)
        self.assertIn("Marks must be a number", page)
        student = sm.get_student("CS101", self.db_path)
        self.assertEqual(student["name"], "Test Student")
        self.assertEqual(student["marks"], 80.0)

    def test_edit_missing_student_redirects_with_message(self):
        response = self.client.get("/edit/NOPE1", follow_redirects=True)
        self.assertIn(b"Student not found", response.data)

    # ----- deleting -----

    def test_delete_page_asks_for_confirmation_and_does_not_delete(self):
        self.add()
        page = self.client.get("/delete/CS101").data.decode()
        self.assertIn("Delete this student?", page)
        self.assertIsNotNone(sm.get_student("CS101", self.db_path))

    def test_delete_student_success(self):
        self.add()
        response = self.post("/delete/CS101")
        self.assertIn(b"deleted successfully", response.data)
        self.assertIsNone(sm.get_student("CS101", self.db_path))

    def test_delete_missing_student_shows_error(self):
        response = self.post("/delete/NOPE1")
        self.assertIn(b"Student not found", response.data)

    # ----- safety and persistence -----

    def test_post_without_csrf_token_is_rejected(self):
        response = self.client.post("/add", data={
            "roll_number": "CS101", "name": "Test Student",
            "course": "Course", "marks": "80",
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(sm.get_all_students(self.db_path), [])

    def test_delete_with_wrong_csrf_token_is_rejected(self):
        self.add()
        response = self.client.post("/delete/CS101", data={"csrf_token": "wrong"})
        self.assertEqual(response.status_code, 400)
        self.assertIsNotNone(sm.get_student("CS101", self.db_path))

    def test_data_survives_website_restart(self):
        self.add()
        restarted = create_app(self.db_path).test_client()  # a brand-new website object
        self.assertIn(b"Test Student", restarted.get("/students").data)

    def test_html_in_student_name_is_escaped(self):
        # The validator blocks "<" in names, but the course field allows it.
        self.add(course="<b>Bold</b>")
        page = self.client.get("/students").data.decode()
        self.assertNotIn("<b>Bold</b>", page)
        self.assertIn("&lt;b&gt;Bold&lt;/b&gt;", page)


if __name__ == "__main__":
    unittest.main()
