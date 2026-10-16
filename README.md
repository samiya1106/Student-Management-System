# Student Management System using Python and DevOps

## Abstract
This project is a simple menu-driven Student Management System written in Python
with SQLite storage. It also demonstrates basic DevOps practices: Git version
control, automated testing with `unittest`, a Jenkins CI pipeline, and an
automated deployment-preparation script. A Flask website (blue-and-white theme)
lets you use the same student database from a web browser.

## Objectives
- Build a working CRUD application using Python and SQLite.
- Write automated tests that never touch real data.
- Use Git for version control.
- Use Jenkins to run tests automatically and stop the pipeline when tests fail.
- Use a script to prepare a deployment folder safely.

## Technologies Used
Python 3, Flask (website), SQLite, unittest, Git, Jenkins, Windows batch scripting.

## Features
1. Add a student (roll number, name, course, marks).
2. Display all students.
3. Search a student by roll number.
4. Update student details (press Enter to keep a value).
5. Delete a student (with confirmation).
6. Input validation and duplicate roll number prevention (case-insensitive).
7. Permanent storage in SQLite (`data/students.db`).
8. Clear "Success:" and "Error:" messages.
9. Simple command-line menu.
10. **Website:** dashboard, add, view, search (roll number, name or course), edit,
    delete with confirmation, form validation and flash messages.

## Project Folder Structure
```
Student-Management-System/
├── student_management.py        (database functions + terminal menu)
├── app.py                       (Flask website)
├── templates/
│   ├── base.html                (page layout and navigation)
│   ├── index.html               (dashboard)
│   ├── students.html            (student list and search results)
│   ├── form.html                (add and edit form)
│   ├── confirm_delete.html      (delete confirmation)
│   ├── error.html               (404 and expired-form pages)
│   └── _table.html              (shared student table)
├── static/
│   └── style.css                (blue-and-white theme)
├── test_student_management.py   (26 original tests)
├── test_app.py                  (search + website tests)
├── Jenkinsfile                  (CI pipeline)
├── requirements.txt             (Flask)
├── deploy.bat                   (deployment preparation)
├── README.md
├── .gitignore
├── data/                        (database is created here)
└── tests/                       (reserved for extra tests)
```

## Prerequisites
- Windows 10/11
- Python 3.8 or newer, added to PATH (check: `python --version`)
- Git for Windows (check: `git --version`)
- Jenkins (only for the CI part) and Java 17 or 21 (the Jenkins installer will tell you)

## Installation Steps
1. Extract the ZIP to e.g. `C:\Student-Management-System`.
2. Open Command Prompt in that folder.
3. The terminal app needs nothing extra. The website needs Flask:
   `pip install -r requirements.txt` (on Linux use a virtual environment, see below).

## How to Run the Application
```
cd C:\Student-Management-System
python student_management.py
```
If `python` is not recognized, try `py student_management.py`.

## How to Run Automated Tests
```
python -m unittest discover -s . -p "test_*.py" -v
```
Tests use a temporary database that is deleted afterwards. Your real data is never touched.

## Website (Flask)

The website uses the same functions and the same database (`data/students.db`)
as the terminal application, so both always show the same students.

**Linux (and macOS):**
```
cd Student-Management-System
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```
Then open **http://127.0.0.1:5000** in your browser. Stop the server with `Ctrl + C`.
Next time, only run `source venv/bin/activate` and `python app.py`.

**Windows:**
```
cd C:\Student-Management-System
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Pages: Dashboard (`/`), Students and search (`/students?q=...`), Add (`/add`),
Edit (`/edit/<roll>`), Delete confirmation (`/delete/<roll>`).

Notes:
- Set your own secret key for real use: `export SECRET_KEY="a-long-random-text"`.
- Roll numbers cannot be changed when editing (they identify the student).
- The website only listens on your own computer (127.0.0.1). It uses Flask's
  development server, which is fine for learning but not for the public internet.
- The page layout uses plain CSS only, so it works without internet access.

## Git Version Control
```
git init
git branch -M main
git add .
git commit -m "Initial commit: Student Management System"
git log --oneline
```
If Git asks who you are:
```
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
```
GitHub is optional. Everything works with a local repository.

## How to Configure and Run the Jenkins Pipeline
1. Install Git, Python (for all users, added to the system PATH), and Jenkins (LTS, Windows installer).
2. Restart the Jenkins service after installing Python so it sees the PATH
   (Services app -> Jenkins -> Restart).
3. Open http://localhost:8080, unlock Jenkins, install suggested plugins, create an admin user.
4. New Item -> name `Student-Management-System` -> **Pipeline** -> OK.
5. Under **Pipeline**: Definition = **Pipeline script from SCM**, SCM = **Git**,
   Repository URL = `C:/Student-Management-System` (your local repo folder),
   Branch = `*/main`, Script Path = `Jenkinsfile`. Save.
6. Click **Build Now**, then open the build -> **Console Output**.

Pipeline stages: Checkout -> Setup Python Environment -> Install Dependencies ->
Run Automated Tests -> Deployment Preparation.

**To see the pipeline fail on purpose:** change one expected value in a test, commit,
and build again. The Tests stage fails and Deployment Preparation is skipped.
Undo the change and commit again to get a green build.

## How Deployment Works
`deploy.bat` creates the deployment folder (default
`%USERPROFILE%\StudentManagementSystem_Deploy`; Jenkins uses
`C:\StudentManagementSystem_Deploy`), copies `student_management.py`,
`requirements.txt`, `README.md`, `app.py`, the `templates` and `static` folders, creates `run_app.bat` and `run_website.bat`, and creates an empty `data` folder if
missing. It never deletes files and never copies or overwrites the database.

Run manually:
```
deploy.bat
deploy.bat "C:\MyDeployFolder"
```
Start the deployed terminal app: `C:\StudentManagementSystem_Deploy\run_app.bat`
Start the deployed website: `C:\StudentManagementSystem_Deploy\run_website.bat` (Flask must be installed)

**Important:** this is *automated deployment preparation*, not full Continuous
Deployment. The pipeline prepares a folder, but nothing restarts a live service or
publishes to a server.

## Expected Outputs (should look similar; verify on your machine)
- Tests: many lines ending with `ok`, then `Ran 55 tests in ...s` and `OK` (26 terminal-app tests, 7 search tests, 22 website tests).
- App: the menu, then messages like `Success: Student added successfully.` or
  `Error: Roll number CS101 already exists.`
- Deployment: `DEPLOYMENT PREPARED SUCCESSFULLY.`
- Jenkins: a green build, ending with `Finished: SUCCESS`.

## Troubleshooting
- **'python' is not recognized / opens Microsoft Store:** install Python from python.org,
  tick "Add Python to PATH", disable the Store alias in
  Settings -> Apps -> Advanced app settings -> App execution aliases, restart Jenkins.
- **Jenkins: 'git' not found:** install Git for Windows and restart Jenkins.
- **Jenkins: "dubious ownership" Git error:** run as administrator:
  `git config --system --add safe.directory C:/Student-Management-System`
- **Jenkins: `checkout scm` fails:** the job must use "Pipeline script from SCM", not a pasted script.
- **Jenkins: branch not found:** your branch may be `master`; change the Branch field or run `git branch -M main`.
- **`No module named flask`:** activate your virtual environment and run `pip install -r requirements.txt`.
- **`externally-managed-environment` error on Linux:** use a virtual environment (`python3 -m venv venv`).
- **Port 5000 already in use:** close the other program, or on macOS turn off AirPlay Receiver.
- **Form shows "Form expired":** refresh the page and submit again.
- **Jenkins stage `Install Dependencies` fails:** the Jenkins machine needs internet access to download Flask.
- **Access denied in deploy.bat:** pass a folder you can write to, e.g. `deploy.bat "%USERPROFILE%\sms_deploy"`.

## Conclusion
The project shows a complete beginner-level DevOps workflow: code is versioned with
Git, tested automatically, built by a Jenkins pipeline that stops on failure, and
prepared for deployment by a safe script.
