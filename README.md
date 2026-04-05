# Python + SQLite School Management System

This is a Python and SQLite version of the School Staff and Student Management System.

## Requirements
- Python 3.14 or newer
- Flask

## Setup
1. Open PowerShell and change directory:
   ```powershell
   cd "c:\dbms project\python_school_project"
   ```
2. Install dependencies:
   ```powershell
   py -m pip install -r requirements.txt
   ```
3. Run the application:
   ```powershell
   py app.py
   ```
4. Open your browser and visit:
   ```text
   http://127.0.0.1:5000
   ```

## Login credentials
- Admin: `admin` / `admin`
- Student: `john@student.com` / `password`

## Notes
- The app uses SQLite and creates `school.db` automatically when first run.
- Admin users can manage students, staff, section assignments, fees, salaries, and room allocations.
- Student users can view the available data.
