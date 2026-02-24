import os
import csv
from io import BytesIO, StringIO
from datetime import datetime
from flask import (
    Flask, render_template_string, redirect, url_for,
    flash, request, send_file
)
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager, UserMixin, login_user, login_required,
    logout_user, current_user
)
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf import FlaskForm
from wtforms import (
    StringField, PasswordField, SelectField, DateField,
    TextAreaField, SubmitField
)
from wtforms.validators import DataRequired, Email, Length, ValidationError

# -------------------------------------------------------------------
# App Configuration
# -------------------------------------------------------------------
app = Flask(__name__)
app.config['SECRET_KEY'] = 'change-this-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///students.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# -------------------------------------------------------------------
# Database Models
# -------------------------------------------------------------------
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    roll_number = db.Column(db.String(20), unique=True, nullable=False)
    department = db.Column(db.String(50), nullable=False)
    semester = db.Column(db.String(10), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    phone = db.Column(db.String(15), nullable=False)
    address = db.Column(db.Text, nullable=False)
    dob = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# -------------------------------------------------------------------
# Forms
# -------------------------------------------------------------------
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class StudentForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    roll_number = StringField('Roll Number', validators=[DataRequired(), Length(max=20)])
    department = SelectField('Department', choices=[
        ('CSE', 'Computer Science'),
        ('ECE', 'Electronics'),
        ('ME', 'Mechanical'),
        ('CE', 'Civil')
    ], validators=[DataRequired()])
    semester = SelectField('Semester', choices=[
        ('1', 'Semester 1'), ('2', 'Semester 2'),
        ('3', 'Semester 3'), ('4', 'Semester 4')
    ], validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone', validators=[DataRequired(), Length(max=15)])
    address = TextAreaField('Address', validators=[DataRequired()])
    dob = DateField('Date of Birth', format='%Y-%m-%d', validators=[DataRequired()])
    submit = SubmitField('Submit')

    def validate_roll_number(self, roll_number):
        student = Student.query.filter_by(roll_number=roll_number.data).first()
        if student:
            raise ValidationError('Roll number already exists.')

    def validate_email(self, email):
        student = Student.query.filter_by(email=email.data).first()
        if student:
            raise ValidationError('Email already registered.')

class SearchForm(FlaskForm):
    search = StringField('Search', validators=[DataRequired()])
    search_by = SelectField('Search By', choices=[
        ('name', 'Name'),
        ('roll', 'Roll Number'),
        ('dept', 'Department')
    ])
    submit = SubmitField('Search')

# -------------------------------------------------------------------
# User Loader
# -------------------------------------------------------------------
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# -------------------------------------------------------------------
# Helper: Render page with base layout
# -------------------------------------------------------------------
def render_page(content_template, title="Dashboard", **context):
    """Render a content template inside the base layout."""
    content_html = render_template_string(content_template, **context)
    return render_template_string(BASE_HTML, content=content_html, page_title=title, **context)

# -------------------------------------------------------------------
# Embedded HTML Templates (as multi-line strings)
# -------------------------------------------------------------------
BASE_HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Student Management - {{ page_title }}</title>
    <!-- Bootstrap 5 CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <!-- Font Awesome -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <!-- Google Fonts -->
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --primary: #6366f1;
            --primary-dark: #4f52e0;
            --primary-light: #8183f5;
            --secondary: #10b981;
            --dark: #1e293b;
            --light: #f8fafc;
            --gray: #94a3b8;
            --card-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.05), 0 8px 10px -6px rgba(0, 0, 0, 0.02);
            --hover-shadow: 0 20px 30px -10px rgba(99, 102, 241, 0.2);
        }
        body {
            font-family: 'Inter', sans-serif;
            background: #f1f5f9;
            color: var(--dark);
            transition: background 0.3s, color 0.3s;
        }
        #wrapper {
            overflow-x: hidden;
        }
        #sidebar-wrapper {
            min-height: 100vh;
            width: 280px;
            transition: margin 0.25s ease-out;
            background: linear-gradient(180deg, var(--primary) 0%, #4f46e5 100%);
            color: white;
            box-shadow: 4px 0 15px rgba(0, 0, 0, 0.1);
        }
        #sidebar-wrapper .sidebar-heading {
            font-weight: 700;
            font-size: 1.5rem;
            letter-spacing: 1px;
            border-bottom: 1px solid rgba(255,255,255,0.2);
            color: white;
        }
        #sidebar-wrapper .list-group-item {
            border: none;
            padding: 15px 25px;
            font-weight: 500;
            background: transparent;
            color: rgba(255,255,255,0.8);
            transition: all 0.2s;
        }
        #sidebar-wrapper .list-group-item:hover {
            background: rgba(255,255,255,0.15);
            color: white;
            transform: translateX(5px);
        }
        #sidebar-wrapper .list-group-item i {
            width: 24px;
            font-size: 1.2rem;
        }
        #page-content-wrapper {
            min-width: 0;
            width: 100%;
            background: #f1f5f9;
        }
        #wrapper.toggled #sidebar-wrapper {
            margin-left: -280px;
        }
        /* Navbar */
        .navbar {
            background: white !important;
            border-radius: 20px;
            margin: 20px 30px;
            padding: 15px 25px;
            box-shadow: var(--card-shadow);
        }
        #menu-toggle {
            cursor: pointer;
            color: var(--primary);
        }
        /* Cards */
        .stat-card {
            background: white;
            border-radius: 20px;
            padding: 1.5rem;
            box-shadow: var(--card-shadow);
            transition: all 0.3s;
            border: 1px solid rgba(0,0,0,0.02);
        }
        .stat-card:hover {
            transform: translateY(-5px);
            box-shadow: var(--hover-shadow);
        }
        .stat-icon {
            width: 60px;
            height: 60px;
            border-radius: 18px;
            background: linear-gradient(135deg, var(--primary-light), var(--primary));
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.8rem;
        }
        /* Tables */
        .table-container {
            background: white;
            border-radius: 20px;
            padding: 1.5rem;
            box-shadow: var(--card-shadow);
        }
        .table {
            margin-bottom: 0;
        }
        .table thead th {
            border-bottom: 2px solid #e2e8f0;
            color: var(--primary);
            font-weight: 600;
            text-transform: uppercase;
            font-size: 0.8rem;
            letter-spacing: 0.5px;
        }
        .table tbody tr:hover {
            background: #f8fafc;
        }
        .btn-primary {
            background: var(--primary);
            border: none;
            border-radius: 12px;
            padding: 8px 20px;
            font-weight: 500;
            transition: all 0.2s;
        }
        .btn-primary:hover {
            background: var(--primary-dark);
            transform: scale(1.02);
        }
        .btn-warning {
            background: #f59e0b;
            border: none;
            border-radius: 10px;
            color: white;
        }
        .btn-danger {
            background: #ef4444;
            border: none;
            border-radius: 10px;
        }
        .badge {
            padding: 6px 12px;
            border-radius: 30px;
            font-weight: 500;
        }
        /* Dark mode */
        body.dark-mode {
            background: #0f172a;
            color: #e2e8f0;
        }
        body.dark-mode #page-content-wrapper {
            background: #0f172a;
        }
        body.dark-mode .navbar {
            background: #1e293b !important;
            color: #e2e8f0;
        }
        body.dark-mode .stat-card,
        body.dark-mode .table-container {
            background: #1e293b;
            color: #e2e8f0;
            border-color: #334155;
        }
        body.dark-mode .table {
            color: #e2e8f0;
        }
        body.dark-mode .table thead th {
            border-color: #334155;
        }
        body.dark-mode .table tbody tr:hover {
            background: #2d3a4f;
        }
        body.dark-mode .btn-outline-secondary {
            color: #e2e8f0;
            border-color: #475569;
        }
        /* Responsive */
        @media (max-width: 768px) {
            #sidebar-wrapper {
                margin-left: -280px;
            }
            #wrapper.toggled #sidebar-wrapper {
                margin-left: 0;
            }
            .navbar {
                margin: 15px;
            }
        }
    </style>
</head>
<body>
    <div class="d-flex" id="wrapper">
        <!-- Sidebar -->
        <div class="shadow" id="sidebar-wrapper">
            <div class="sidebar-heading text-center py-4">
                <i class="fas fa-graduation-cap me-2"></i>EduManage
            </div>
            <div class="list-group list-group-flush">
                <a href="{{ url_for('dashboard') }}" class="list-group-item">
                    <i class="fas fa-tachometer-alt me-3"></i>Dashboard
                </a>
                <a href="{{ url_for('add_student') }}" class="list-group-item">
                    <i class="fas fa-user-plus me-3"></i>Add Student
                </a>
                <a href="{{ url_for('view_students') }}" class="list-group-item">
                    <i class="fas fa-users me-3"></i>View Students
                </a>
                <a href="{{ url_for('search') }}" class="list-group-item">
                    <i class="fas fa-search me-3"></i>Search Student
                </a>
                <a href="{{ url_for('export_csv') }}" class="list-group-item">
                    <i class="fas fa-download me-3"></i>Reports (CSV)
                </a>
                <a href="{{ url_for('logout') }}" class="list-group-item">
                    <i class="fas fa-sign-out-alt me-3"></i>Logout
                </a>
            </div>
        </div>

        <!-- Page Content -->
        <div id="page-content-wrapper">
            <nav class="navbar navbar-expand-lg">
                <div class="container-fluid">
                    <div class="d-flex align-items-center">
                        <i class="fas fa-bars fs-4 me-3" id="menu-toggle"></i>
                        <h4 class="mb-0">{{ page_title }}</h4>
                    </div>
                    <div class="d-flex align-items-center">
                        <div class="dropdown me-3">
                            <a class="text-dark text-decoration-none dropdown-toggle" href="#" id="profileDropdown" data-bs-toggle="dropdown">
                                <i class="fas fa-user-circle fs-4" style="color: var(--primary);"></i> <span class="fw-semibold">Admin</span>
                            </a>
                            <ul class="dropdown-menu dropdown-menu-end">
                                <li><a class="dropdown-item" href="#">Profile</a></li>
                                <li><a class="dropdown-item" href="{{ url_for('logout') }}">Logout</a></li>
                            </ul>
                        </div>
                        <span class="me-3 text-muted" id="current-datetime"></span>
                        <button class="btn btn-sm btn-outline-secondary rounded-circle" id="darkModeToggle">
                            <i class="fas fa-moon"></i>
                        </button>
                    </div>
                </div>
            </nav>

            <div class="container-fluid px-4">
                {% with messages = get_flashed_messages(with_categories=true) %}
                    {% if messages %}
                        {% for category, message in messages %}
                            <div class="alert alert-{{ category }} alert-dismissible fade show" role="alert">
                                {{ message }}
                                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                            </div>
                        {% endfor %}
                    {% endif %}
                {% endwith %}

                {{ content|safe }}
            </div>
        </div>
    </div>

    <!-- Bootstrap JS -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <!-- Chart.js -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script>
        // Toggle sidebar
        const menuToggle = document.getElementById('menu-toggle');
        const wrapper = document.getElementById('wrapper');
        menuToggle.addEventListener('click', () => {
            wrapper.classList.toggle('toggled');
        });

        // Update datetime
        function updateDateTime() {
            const now = new Date();
            const formatted = now.toLocaleString('en-US', { dateStyle: 'medium', timeStyle: 'short' });
            document.getElementById('current-datetime').textContent = formatted;
        }
        setInterval(updateDateTime, 1000);
        updateDateTime();

        // Dark mode toggle
        const darkModeToggle = document.getElementById('darkModeToggle');
        const body = document.body;
        if (localStorage.getItem('darkMode') === 'enabled') {
            body.classList.add('dark-mode');
            darkModeToggle.innerHTML = '<i class="fas fa-sun"></i>';
        }
        darkModeToggle.addEventListener('click', function() {
            body.classList.toggle('dark-mode');
            if (body.classList.contains('dark-mode')) {
                localStorage.setItem('darkMode', 'enabled');
                darkModeToggle.innerHTML = '<i class="fas fa-sun"></i>';
            } else {
                localStorage.setItem('darkMode', 'disabled');
                darkModeToggle.innerHTML = '<i class="fas fa-moon"></i>';
            }
        });
    </script>
</body>
</html>
'''

LOGIN_HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login - Student Management</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        body {
            font-family: 'Inter', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            height: 100vh;
            display: flex;
            align-items: center;
        }
        .login-card {
            border-radius: 24px;
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
            border: none;
            overflow: hidden;
        }
        .login-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 2rem;
            text-align: center;
        }
        .btn-login {
            background: #667eea;
            border: none;
            border-radius: 12px;
            padding: 12px;
            font-weight: 600;
            transition: all 0.2s;
        }
        .btn-login:hover {
            background: #5a67d8;
            transform: translateY(-2px);
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="row justify-content-center">
            <div class="col-md-6 col-lg-5">
                <div class="card login-card">
                    <div class="login-header">
                        <h3 class="fw-bold">Student Management</h3>
                        <p class="mb-0">Admin Login</p>
                    </div>
                    <div class="card-body p-4">
                        {% with messages = get_flashed_messages(with_categories=true) %}
                            {% if messages %}
                                {% for category, message in messages %}
                                    <div class="alert alert-{{ category }}">{{ message }}</div>
                                {% endfor %}
                            {% endif %}
                        {% endwith %}
                        <form method="POST">
                            {{ form.hidden_tag() }}
                            <div class="mb-3">
                                {{ form.username.label(class="form-label fw-semibold") }}
                                {{ form.username(class="form-control form-control-lg") }}
                            </div>
                            <div class="mb-4">
                                {{ form.password.label(class="form-label fw-semibold") }}
                                {{ form.password(class="form-control form-control-lg") }}
                            </div>
                            <button type="submit" class="btn btn-login btn-primary w-100 btn-lg">Login</button>
                        </form>
                    </div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
'''

DASHBOARD_HTML = '''
<div class="row g-4 my-2">
    <div class="col-md-3">
        <div class="stat-card d-flex align-items-center">
            <div class="stat-icon me-3">
                <i class="fas fa-user-graduate"></i>
            </div>
            <div>
                <h3 class="fs-2 fw-bold mb-0">{{ total_students }}</h3>
                <p class="text-muted mb-0">Total Students</p>
            </div>
        </div>
    </div>
    <div class="col-md-3">
        <div class="stat-card d-flex align-items-center">
            <div class="stat-icon me-3">
                <i class="fas fa-building"></i>
            </div>
            <div>
                <h3 class="fs-2 fw-bold mb-0">{{ departments }}</h3>
                <p class="text-muted mb-0">Departments</p>
            </div>
        </div>
    </div>
    <div class="col-md-3">
        <div class="stat-card d-flex align-items-center">
            <div class="stat-icon me-3">
                <i class="fas fa-book-open"></i>
            </div>
            <div>
                <h3 class="fs-2 fw-bold mb-0">{{ current_semester }}</h3>
                <p class="text-muted mb-0">Current Semester</p>
            </div>
        </div>
    </div>
    <div class="col-md-3">
        <div class="stat-card d-flex align-items-center">
            <div class="stat-icon me-3">
                <i class="fas fa-clock"></i>
            </div>
            <div>
                <h3 class="fs-2 fw-bold mb-0">{{ recent|length }}</h3>
                <p class="text-muted mb-0">Recently Added</p>
            </div>
        </div>
    </div>
</div>

<div class="row my-5">
    <div class="col">
        <div class="table-container">
            <h5 class="fw-semibold mb-4">Recent Students</h5>
            <div class="table-responsive">
                <table class="table table-hover align-middle">
                    <thead>
                        <tr>
                            <th>Name</th>
                            <th>Roll No</th>
                            <th>Department</th>
                            <th>Semester</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for student in recent %}
                        <tr>
                            <td><span class="fw-medium">{{ student.name }}</span></td>
                            <td>{{ student.roll_number }}</td>
                            <td><span class="badge bg-primary bg-opacity-10 text-primary">{{ student.department }}</span></td>
                            <td>{{ student.semester }}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</div>

<div class="row g-4">
    <div class="col-md-6">
        <div class="table-container">
            <h5 class="fw-semibold mb-4">Students by Department</h5>
            <canvas id="deptChart" height="200"></canvas>
        </div>
    </div>
    <div class="col-md-6">
        <div class="table-container">
            <h5 class="fw-semibold mb-4">Students by Semester</h5>
            <canvas id="semesterChart" height="200"></canvas>
        </div>
    </div>
</div>

<script>
    // Example charts – replace with real data if needed
    const deptCtx = document.getElementById('deptChart').getContext('2d');
    new Chart(deptCtx, {
        type: 'doughnut',
        data: {
            labels: ['CSE', 'ECE', 'ME', 'CE'],
            datasets: [{
                data: [12, 8, 5, 7],
                backgroundColor: ['#6366f1', '#10b981', '#f59e0b', '#ef4444'],
                borderWidth: 0
            }]
        },
        options: {
            cutout: '70%',
            plugins: { legend: { position: 'bottom' } }
        }
    });

    const semCtx = document.getElementById('semesterChart').getContext('2d');
    new Chart(semCtx, {
        type: 'bar',
        data: {
            labels: ['Sem 1', 'Sem 2', 'Sem 3', 'Sem 4'],
            datasets: [{
                label: 'Number of Students',
                data: [10, 8, 7, 9],
                backgroundColor: '#6366f1',
                borderRadius: 8
            }]
        },
        options: {
            scales: { y: { beginAtZero: true, grid: { display: false } } },
            plugins: { legend: { display: false } }
        }
    });
</script>
'''

ADD_STUDENT_HTML = '''
<div class="row">
    <div class="col-lg-8 mx-auto">
        <div class="table-container">
            <h5 class="fw-semibold mb-4"><i class="fas fa-user-plus me-2 text-primary"></i>Add New Student</h5>
            <form method="POST" novalidate>
                {{ form.hidden_tag() }}
                <div class="row">
                    <div class="col-md-6 mb-3">
                        {{ form.name.label(class="form-label fw-medium") }}
                        {{ form.name(class="form-control" + (" is-invalid" if form.name.errors else "")) }}
                        {% for error in form.name.errors %}<div class="invalid-feedback">{{ error }}</div>{% endfor %}
                    </div>
                    <div class="col-md-6 mb-3">
                        {{ form.roll_number.label(class="form-label fw-medium") }}
                        {{ form.roll_number(class="form-control" + (" is-invalid" if form.roll_number.errors else "")) }}
                        {% for error in form.roll_number.errors %}<div class="invalid-feedback">{{ error }}</div>{% endfor %}
                    </div>
                </div>
                <div class="row">
                    <div class="col-md-6 mb-3">
                        {{ form.department.label(class="form-label fw-medium") }}
                        {{ form.department(class="form-select" + (" is-invalid" if form.department.errors else "")) }}
                        {% for error in form.department.errors %}<div class="invalid-feedback">{{ error }}</div>{% endfor %}
                    </div>
                    <div class="col-md-6 mb-3">
                        {{ form.semester.label(class="form-label fw-medium") }}
                        {{ form.semester(class="form-select" + (" is-invalid" if form.semester.errors else "")) }}
                        {% for error in form.semester.errors %}<div class="invalid-feedback">{{ error }}</div>{% endfor %}
                    </div>
                </div>
                <div class="row">
                    <div class="col-md-6 mb-3">
                        {{ form.email.label(class="form-label fw-medium") }}
                        {{ form.email(class="form-control" + (" is-invalid" if form.email.errors else "")) }}
                        {% for error in form.email.errors %}<div class="invalid-feedback">{{ error }}</div>{% endfor %}
                    </div>
                    <div class="col-md-6 mb-3">
                        {{ form.phone.label(class="form-label fw-medium") }}
                        {{ form.phone(class="form-control" + (" is-invalid" if form.phone.errors else "")) }}
                        {% for error in form.phone.errors %}<div class="invalid-feedback">{{ error }}</div>{% endfor %}
                    </div>
                </div>
                <div class="mb-3">
                    {{ form.address.label(class="form-label fw-medium") }}
                    {{ form.address(class="form-control" + (" is-invalid" if form.address.errors else ""), rows=3) }}
                    {% for error in form.address.errors %}<div class="invalid-feedback">{{ error }}</div>{% endfor %}
                </div>
                <div class="mb-4">
                    {{ form.dob.label(class="form-label fw-medium") }}
                    {{ form.dob(class="form-control" + (" is-invalid" if form.dob.errors else ""), type="date") }}
                    {% for error in form.dob.errors %}<div class="invalid-feedback">{{ error }}</div>{% endfor %}
                </div>
                <button type="submit" class="btn btn-primary px-4">{{ form.submit.label.text }}</button>
                <a href="{{ url_for('view_students') }}" class="btn btn-outline-secondary px-4 ms-2">Cancel</a>
            </form>
        </div>
    </div>
</div>
'''

EDIT_STUDENT_HTML = '''
<div class="row">
    <div class="col-lg-8 mx-auto">
        <div class="table-container">
            <h5 class="fw-semibold mb-4"><i class="fas fa-edit me-2 text-warning"></i>Edit Student</h5>
            <form method="POST" novalidate>
                {{ form.hidden_tag() }}
                <div class="row">
                    <div class="col-md-6 mb-3">
                        {{ form.name.label(class="form-label fw-medium") }}
                        {{ form.name(class="form-control" + (" is-invalid" if form.name.errors else "")) }}
                        {% for error in form.name.errors %}<div class="invalid-feedback">{{ error }}</div>{% endfor %}
                    </div>
                    <div class="col-md-6 mb-3">
                        {{ form.roll_number.label(class="form-label fw-medium") }}
                        {{ form.roll_number(class="form-control" + (" is-invalid" if form.roll_number.errors else "")) }}
                        {% for error in form.roll_number.errors %}<div class="invalid-feedback">{{ error }}</div>{% endfor %}
                    </div>
                </div>
                <div class="row">
                    <div class="col-md-6 mb-3">
                        {{ form.department.label(class="form-label fw-medium") }}
                        {{ form.department(class="form-select" + (" is-invalid" if form.department.errors else "")) }}
                        {% for error in form.department.errors %}<div class="invalid-feedback">{{ error }}</div>{% endfor %}
                    </div>
                    <div class="col-md-6 mb-3">
                        {{ form.semester.label(class="form-label fw-medium") }}
                        {{ form.semester(class="form-select" + (" is-invalid" if form.semester.errors else "")) }}
                        {% for error in form.semester.errors %}<div class="invalid-feedback">{{ error }}</div>{% endfor %}
                    </div>
                </div>
                <div class="row">
                    <div class="col-md-6 mb-3">
                        {{ form.email.label(class="form-label fw-medium") }}
                        {{ form.email(class="form-control" + (" is-invalid" if form.email.errors else "")) }}
                        {% for error in form.email.errors %}<div class="invalid-feedback">{{ error }}</div>{% endfor %}
                    </div>
                    <div class="col-md-6 mb-3">
                        {{ form.phone.label(class="form-label fw-medium") }}
                        {{ form.phone(class="form-control" + (" is-invalid" if form.phone.errors else "")) }}
                        {% for error in form.phone.errors %}<div class="invalid-feedback">{{ error }}</div>{% endfor %}
                    </div>
                </div>
                <div class="mb-3">
                    {{ form.address.label(class="form-label fw-medium") }}
                    {{ form.address(class="form-control" + (" is-invalid" if form.address.errors else ""), rows=3) }}
                    {% for error in form.address.errors %}<div class="invalid-feedback">{{ error }}</div>{% endfor %}
                </div>
                <div class="mb-4">
                    {{ form.dob.label(class="form-label fw-medium") }}
                    {{ form.dob(class="form-control" + (" is-invalid" if form.dob.errors else ""), type="date") }}
                    {% for error in form.dob.errors %}<div class="invalid-feedback">{{ error }}</div>{% endfor %}
                </div>
                <button type="submit" class="btn btn-warning px-4">Update</button>
                <a href="{{ url_for('view_students') }}" class="btn btn-outline-secondary px-4 ms-2">Cancel</a>
            </form>
        </div>
    </div>
</div>
'''

VIEW_STUDENTS_HTML = '''
<div class="d-flex justify-content-between align-items-center mb-4">
    <h5 class="fw-semibold mb-0">All Students</h5>
    <div>
        <a href="{{ url_for('add_student') }}" class="btn btn-primary me-2"><i class="fas fa-plus me-2"></i>Add New</a>
        <a href="{{ url_for('export_csv') }}" class="btn btn-success"><i class="fas fa-download me-2"></i>Export CSV</a>
    </div>
</div>

<div class="row mb-4">
    <div class="col-md-6">
        <form action="{{ url_for('search') }}" method="POST" class="d-flex">
            <input class="form-control me-2" type="search" placeholder="Search by name, roll or department..." name="search" required>
            <button class="btn btn-outline-primary" type="submit"><i class="fas fa-search"></i></button>
        </form>
    </div>
    <div class="col-md-6 text-end">
        <div class="btn-group">
            <button class="btn btn-outline-secondary dropdown-toggle" type="button" data-bs-toggle="dropdown">Filter Semester</button>
            <ul class="dropdown-menu">
                <li><a class="dropdown-item" href="{{ url_for('view_students') }}">All</a></li>
                <li><a class="dropdown-item" href="{{ url_for('filter_by_semester', semester='1') }}">Semester 1</a></li>
                <li><a class="dropdown-item" href="{{ url_for('filter_by_semester', semester='2') }}">Semester 2</a></li>
                <li><a class="dropdown-item" href="{{ url_for('filter_by_semester', semester='3') }}">Semester 3</a></li>
                <li><a class="dropdown-item" href="{{ url_for('filter_by_semester', semester='4') }}">Semester 4</a></li>
            </ul>
        </div>
    </div>
</div>

<div class="table-container">
    <div class="table-responsive">
        <table class="table table-hover align-middle">
            <thead>
                <tr>
                    <th>ID</th><th>Name</th><th>Roll No</th><th>Department</th><th>Semester</th>
                    <th>Email</th><th>Phone</th><th>Actions</th>
                </tr>
            </thead>
            <tbody>
                {% for student in students.items %}
                <tr>
                    <td>{{ student.id }}</td>
                    <td><span class="fw-medium">{{ student.name }}</span></td>
                    <td>{{ student.roll_number }}</td>
                    <td><span class="badge bg-primary bg-opacity-10 text-primary">{{ student.department }}</span></td>
                    <td>{{ student.semester }}</td>
                    <td>{{ student.email }}</td>
                    <td>{{ student.phone }}</td>
                    <td>
                        <a href="{{ url_for('edit_student', id=student.id) }}" class="btn btn-sm btn-warning me-1"><i class="fas fa-edit"></i></a>
                        <button class="btn btn-sm btn-danger" data-bs-toggle="modal" data-bs-target="#deleteModal{{ student.id }}"><i class="fas fa-trash"></i></button>
                    </td>
                </tr>
                <!-- Delete Modal -->
                <div class="modal fade" id="deleteModal{{ student.id }}" tabindex="-1">
                    <div class="modal-dialog">
                        <div class="modal-content">
                            <div class="modal-header">
                                <h5 class="modal-title">Confirm Delete</h5>
                                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                            </div>
                            <div class="modal-body">
                                Are you sure you want to delete <strong>{{ student.name }}</strong> ({{ student.roll_number }})?
                            </div>
                            <div class="modal-footer">
                                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                                <form action="{{ url_for('delete_student', id=student.id) }}" method="POST" style="display:inline;">
                                    <button type="submit" class="btn btn-danger">Delete</button>
                                </form>
                            </div>
                        </div>
                    </div>
                </div>
                {% endfor %}
            </tbody>
        </table>
    </div>

    <!-- Pagination -->
    <nav aria-label="Page navigation" class="mt-4">
        <ul class="pagination justify-content-center">
            {% if students.has_prev %}
                <li class="page-item"><a class="page-link" href="{{ url_for('view_students', page=students.prev_num) }}">Previous</a></li>
            {% else %}
                <li class="page-item disabled"><span class="page-link">Previous</span></li>
            {% endif %}

            {% for page_num in students.iter_pages(left_edge=1, right_edge=1, left_current=1, right_current=2) %}
                {% if page_num %}
                    {% if page_num == students.page %}
                        <li class="page-item active"><span class="page-link">{{ page_num }}</span></li>
                    {% else %}
                        <li class="page-item"><a class="page-link" href="{{ url_for('view_students', page=page_num) }}">{{ page_num }}</a></li>
                    {% endif %}
                {% else %}
                    <li class="page-item disabled"><span class="page-link">...</span></li>
                {% endif %}
            {% endfor %}

            {% if students.has_next %}
                <li class="page-item"><a class="page-link" href="{{ url_for('view_students', page=students.next_num) }}">Next</a></li>
            {% else %}
                <li class="page-item disabled"><span class="page-link">Next</span></li>
            {% endif %}
        </ul>
    </nav>
</div>
'''

SEARCH_HTML = '''
<div class="row">
    <div class="col-md-6 mx-auto">
        <div class="table-container">
            <h5 class="fw-semibold mb-4"><i class="fas fa-search me-2 text-info"></i>Search Students</h5>
            <form method="POST">
                {{ form.hidden_tag() }}
                <div class="mb-3">
                    {{ form.search.label(class="form-label fw-medium") }}
                    {{ form.search(class="form-control") }}
                </div>
                <div class="mb-4">
                    {{ form.search_by.label(class="form-label fw-medium") }}
                    {{ form.search_by(class="form-select") }}
                </div>
                <button type="submit" class="btn btn-info text-white px-4">Search</button>
            </form>
        </div>
    </div>
</div>

{% if results is defined and results %}
<div class="row mt-4">
    <div class="col">
        <div class="table-container">
            <h5 class="fw-semibold mb-4">Results ({{ results|length }})</h5>
            <div class="table-responsive">
                <table class="table table-hover align-middle">
                    <thead>
                        <tr><th>Name</th><th>Roll</th><th>Department</th><th>Semester</th><th>Actions</th></tr>
                    </thead>
                    <tbody>
                        {% for student in results %}
                        <tr>
                            <td><span class="fw-medium">{{ student.name }}</span></td>
                            <td>{{ student.roll_number }}</td>
                            <td><span class="badge bg-primary bg-opacity-10 text-primary">{{ student.department }}</span></td>
                            <td>{{ student.semester }}</td>
                            <td>
                                <a href="{{ url_for('edit_student', id=student.id) }}" class="btn btn-sm btn-warning">Edit</a>
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</div>
{% endif %}
'''

# -------------------------------------------------------------------
# Routes
# -------------------------------------------------------------------
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user)
            flash('Logged in successfully!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'danger')
    return render_template_string(LOGIN_HTML, form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    total_students = Student.query.count()
    departments = db.session.query(Student.department).distinct().count()
    # For demonstration, count students with semester '3' as "current semester"
    current_semester = Student.query.filter_by(semester='3').count()
    recent = Student.query.order_by(Student.created_at.desc()).limit(5).all()
    return render_page(DASHBOARD_HTML, title="Dashboard",
                       total_students=total_students,
                       departments=departments,
                       current_semester=current_semester,
                       recent=recent)

@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_student():
    form = StudentForm()
    if form.validate_on_submit():
        student = Student(
            name=form.name.data,
            roll_number=form.roll_number.data,
            department=form.department.data,
            semester=form.semester.data,
            email=form.email.data,
            phone=form.phone.data,
            address=form.address.data,
            dob=form.dob.data
        )
        try:
            db.session.add(student)
            db.session.commit()
            flash('Student added successfully!', 'success')
            return redirect(url_for('view_students'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')
    return render_page(ADD_STUDENT_HTML, title="Add Student", form=form)

@app.route('/students')
@login_required
def view_students():
    page = request.args.get('page', 1, type=int)
    per_page = 5
    students = Student.query.order_by(Student.created_at.desc()).paginate(page=page, per_page=per_page)
    return render_page(VIEW_STUDENTS_HTML, title="View Students", students=students)

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_student(id):
    student = Student.query.get_or_404(id)
    form = StudentForm(obj=student)
    if form.validate_on_submit():
        student.name = form.name.data
        student.roll_number = form.roll_number.data
        student.department = form.department.data
        student.semester = form.semester.data
        student.email = form.email.data
        student.phone = form.phone.data
        student.address = form.address.data
        student.dob = form.dob.data
        try:
            db.session.commit()
            flash('Student updated successfully!', 'success')
            return redirect(url_for('view_students'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')
    return render_page(EDIT_STUDENT_HTML, title="Edit Student", form=form, student=student)

@app.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete_student(id):
    student = Student.query.get_or_404(id)
    db.session.delete(student)
    db.session.commit()
    flash('Student deleted successfully!', 'success')
    return redirect(url_for('view_students'))

@app.route('/search', methods=['GET', 'POST'])
@login_required
def search():
    form = SearchForm()
    results = []
    if request.method == 'POST' and form.validate():
        term = form.search.data
        by = form.search_by.data
        if by == 'name':
            results = Student.query.filter(Student.name.contains(term)).all()
        elif by == 'roll':
            results = Student.query.filter(Student.roll_number.contains(term)).all()
        elif by == 'dept':
            results = Student.query.filter(Student.department.contains(term)).all()
    return render_page(SEARCH_HTML, title="Search Students", form=form, results=results)

@app.route('/export/csv')
@login_required
def export_csv():
    students = Student.query.all()
    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(['ID', 'Name', 'Roll Number', 'Department', 'Semester', 'Email', 'Phone', 'DOB'])
    for s in students:
        cw.writerow([s.id, s.name, s.roll_number, s.department, s.semester, s.email, s.phone, s.dob])
    output = si.getvalue().encode('utf-8')  # Convert to bytes
    si.close()
    return send_file(
        BytesIO(output),
        mimetype='text/csv',
        as_attachment=True,
        download_name='students.csv'
    )

@app.route('/filter/<semester>')
@login_required
def filter_by_semester(semester):
    students_list = Student.query.filter_by(semester=semester).all()
    # Create a simple pagination-like object for template compatibility
    class Pagination:
        def __init__(self, items):
            self.items = items
            self.has_prev = False
            self.has_next = False
            self.page = 1
            self.per_page = len(items)
            self.total = len(items)
        def iter_pages(self, **kwargs):
            return []
    students = Pagination(students_list)
    return render_page(VIEW_STUDENTS_HTML, title=f"Students - Semester {semester}", students=students)

@app.errorhandler(404)
def not_found(e):
    return render_page('''
    <div class="text-center mt-5">
        <h1 class="display-1">404</h1>
        <p class="lead">Page Not Found</p>
        <a href="{{ url_for('dashboard') }}" class="btn btn-primary">Go to Dashboard</a>
    </div>
    ''', title="404 Not Found"), 404

# -------------------------------------------------------------------
# Database initialization and default admin
# -------------------------------------------------------------------
with app.app_context():
    db.create_all()
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', password_hash=generate_password_hash('admin123'))
        db.session.add(admin)
        db.session.commit()

# -------------------------------------------------------------------
# Run the application
# -------------------------------------------------------------------
if __name__ == '__main__':
    app.run(debug=True)