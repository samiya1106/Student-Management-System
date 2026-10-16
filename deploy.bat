@echo off
setlocal

REM ============================================================
REM  deploy.bat - Prepares a deployment folder (safe to re-run)
REM
REM  Usage:
REM    deploy.bat                     (uses default folder below)
REM    deploy.bat "C:\MyDeployFolder" (uses your own folder)
REM
REM  Safety: this script only COPIES a fixed list of files.
REM  It never deletes anything and never copies or overwrites
REM  the data folder, so student records are always preserved.
REM ============================================================

set "SOURCE=%~dp0"
set "TARGET=%USERPROFILE%\StudentManagementSystem_Deploy"
if not "%~1"=="" set "TARGET=%~1"

echo Source folder : %SOURCE%
echo Deploy folder : %TARGET%
echo.

if not exist "%TARGET%" mkdir "%TARGET%"
if errorlevel 1 goto :error

REM Create the data folder if missing (existing contents are left alone).
if not exist "%TARGET%\data" mkdir "%TARGET%\data"
if errorlevel 1 goto :error

echo Copying application files...
copy /Y "%SOURCE%student_management.py" "%TARGET%\student_management.py" >nul
if errorlevel 1 goto :error
copy /Y "%SOURCE%requirements.txt" "%TARGET%\requirements.txt" >nul
if errorlevel 1 goto :error
copy /Y "%SOURCE%README.md" "%TARGET%\README.md" >nul
if errorlevel 1 goto :error
copy /Y "%SOURCE%app.py" "%TARGET%\app.py" >nul
if errorlevel 1 goto :error
xcopy /E /I /Y "%SOURCE%templates" "%TARGET%\templates" >nul
if errorlevel 1 goto :error
xcopy /E /I /Y "%SOURCE%static" "%TARGET%\static" >nul
if errorlevel 1 goto :error

REM Create a small launcher file in the deployment folder.
> "%TARGET%\run_app.bat" echo @echo off
>> "%TARGET%\run_app.bat" echo cd /d "%%~dp0"
>> "%TARGET%\run_app.bat" echo python student_management.py
>> "%TARGET%\run_app.bat" echo pause
if errorlevel 1 goto :error

REM Launcher for the website (Flask must be installed: pip install -r requirements.txt).
> "%TARGET%\run_website.bat" echo @echo off
>> "%TARGET%\run_website.bat" echo cd /d "%%~dp0"
>> "%TARGET%\run_website.bat" echo python app.py
>> "%TARGET%\run_website.bat" echo pause
if errorlevel 1 goto :error

REM Check that the important files really exist.
if not exist "%TARGET%\student_management.py" goto :error
if not exist "%TARGET%\run_app.bat" goto :error
if not exist "%TARGET%\app.py" goto :error
if not exist "%TARGET%\templates\base.html" goto :error
if not exist "%TARGET%\static\style.css" goto :error
if not exist "%TARGET%\data" goto :error

echo.
echo DEPLOYMENT PREPARED SUCCESSFULLY.
echo To start the deployed terminal application, run:
echo     "%TARGET%\run_app.bat"
echo To start the deployed website (then open http://127.0.0.1:5000), run:
echo     "%TARGET%\run_website.bat"
if not defined JENKINS_URL pause
exit /b 0

:error
echo.
echo DEPLOYMENT FAILED. Please check the messages above.
if not defined JENKINS_URL pause
exit /b 1
