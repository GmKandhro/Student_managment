# Student Management (Flask)

A simple, self-contained Student Management web app built with Flask.

## Overview

This project provides a lightweight admin interface to manage students: add, edit, delete, search, filter by semester, view paginated lists, and export student data to CSV. The app uses SQLite (file `students.db`) and includes a default admin user for quick testing.

## Features

- User authentication (Flask-Login)
- Student CRUD (Create, Read, Update, Delete)
- Search and filter students
- Paginated list view
- Export students to CSV
- Responsive UI with Bootstrap and charts for quick stats

## Prerequisites

- Python 3.8+
- Git (optional)

## Recommended Python packages

The app depends on these packages (install with `pip install`):

- Flask
- Flask-Login
- Flask-WTF
- Flask-SQLAlchemy
- WTForms
- Werkzeug

You can create a `requirements.txt` by running:

```bash
pip freeze > requirements.txt
```

## Installation (Windows PowerShell)

1. Clone or copy the repository to your machine.
2. Create and activate a virtual environment:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

3. Install dependencies:

```powershell
pip install Flask Flask-Login Flask-WTF Flask-SQLAlchemy WTForms Werkzeug
```

4. (Optional) Save installed packages:

```powershell
pip freeze > requirements.txt
```

## Configuration

The app configuration is inside `app.py`. Key settings:

- `SECRET_KEY` — change this in production.
- `SQLALCHEMY_DATABASE_URI` — defaults to `sqlite:///students.db`.

To override configuration, either edit `app.py` or set environment variables before running.

## Running the app

Start the application (development mode):

```powershell
# From project root, with virtualenv active
python app.py
```

This starts a development server on `http://127.0.0.1:5000`.

You can also use Flask CLI:

```powershell
$env:FLASK_APP = "app.py"
$env:FLASK_ENV = "development"
flask run
```

## Default Admin Account

On first run the app creates a default admin user:

- Username: `admin`
- Password: `admin123`

Change the password or remove the seeded account before deploying to production.

## Database

- The app uses SQLite and will create `students.db` in the project directory when first run.
- To reset the database, stop the app, delete `students.db`, then restart — the tables and default admin will be recreated.

## Routes / Endpoints

Below are the main routes available in the app (all routes requiring authentication are indicated):

- `/` — Redirects to `/dashboard` (if logged in) or `/login`.
- `/login` [GET, POST] — Login page.
- `/logout` [GET] — Logout (requires login).
- `/dashboard` [GET] — Admin dashboard (requires login).
- `/add` [GET, POST] — Add new student (requires login).
- `/students` [GET] — View paginated students (requires login). Query param: `page` (int).
- `/edit/<id>` [GET, POST] — Edit a student (requires login).
- `/delete/<id>` [POST] — Delete a student (requires login).
- `/search` [GET, POST] — Search students by name/roll/department (requires login).
- `/export/csv` [GET] — Export all students as CSV (requires login).
- `/filter/<semester>` [GET] — View students filtered by semester (requires login).

## Exporting Data

- Use the **Export CSV** button in the UI or visit `/export/csv` (while logged in) to download `students.csv`.

## Security & Production Notes

- The `SECRET_KEY` in `app.py` is for development only; set a secure key in production.
- Use a proper database (Postgres, MySQL) for production deployments.
- Disable `debug=True` and configure a production-ready WSGI server (e.g., Gunicorn, uWSGI) behind a reverse proxy.

## Contributing

Feel free to open issues or pull requests. Suggestions:

- Add unit tests for models and routes.
- Add Docker support and production configuration.
- Improve input validation and error handling.

## License

This project is provided as-is. Add a license file if you plan to share it publicly.

---

Happy hacking — you can find the new README at the project root: [README.md](README.md)
