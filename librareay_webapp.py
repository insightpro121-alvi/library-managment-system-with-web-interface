# library_web_app.py
from flask import Flask, render_template_string, request, redirect, url_for, session, flash
import os
import functools
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'library-management-secret-key-2024'

# Global variables for user management
USERS_FILE = "library_users.txt"
BOOKS_FILE = "library_books.txt"
BORROWS_FILE = "library_borrows.txt"

# ============= BORROW TRACKING FUNCTIONS =============

def load_borrows():
    """Load borrow records from file"""
    borrows = {}
    try:
        if os.path.exists(BORROWS_FILE):
            with open(BORROWS_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        parts = line.split("|")
                        if len(parts) >= 3:
                            username = parts[0]
                            book_id = parts[1]
                            borrow_date = parts[2]
                            return_date = parts[3] if len(parts) > 3 else None
                            
                            if username not in borrows:
                                borrows[username] = []
                            borrows[username].append({
                                'book_id': book_id,
                                'borrow_date': borrow_date,
                                'return_date': return_date if return_date != 'None' else None
                            })
    except Exception as e:
        print(f"❌ Error loading borrows: {e}")
    return borrows

def save_borrows(borrows_dict):
    """Save borrow records to file"""
    try:
        with open(BORROWS_FILE, "w", encoding="utf-8") as f:
            for username, user_borrows in borrows_dict.items():
                for borrow in user_borrows:
                    return_date = borrow['return_date'] if borrow['return_date'] else 'None'
                    f.write(f"{username}|{borrow['book_id']}|{borrow['borrow_date']}|{return_date}\n")
        return True
    except Exception as e:
        print(f"❌ Error saving borrows: {e}")
        return False

def borrow_book_for_user(username, book_id):
    """Borrow a book for specific user"""
    borrows = load_borrows()
    if username not in borrows:
        borrows[username] = []
    
    # Check if user already has this book borrowed and not returned
    for borrow in borrows[username]:
        if borrow['book_id'] == book_id and not borrow['return_date']:
            return False  # Already borrowed and not returned
    
    # Add new borrow record
    borrows[username].append({
        'book_id': book_id,
        'borrow_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'return_date': None
    })
    
    return save_borrows(borrows)

def return_book_for_user(username, book_id):
    """Return a book for specific user"""
    borrows = load_borrows()
    
    if username in borrows:
        for borrow in borrows[username]:
            if borrow['book_id'] == book_id and not borrow['return_date']:
                borrow['return_date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                return save_borrows(borrows)
    return False

def get_user_borrowed_books(username):
    """Get list of books currently borrowed by user"""
    borrows = load_borrows()
    user_borrows = []
    
    if username in borrows:
        for borrow in borrows[username]:
            if not borrow['return_date']:
                user_borrows.append(borrow['book_id'])
    
    return user_borrows

def is_book_borrowed_by_user(username, book_id):
    """Check if specific book is borrowed by user"""
    user_borrows = get_user_borrowed_books(username)
    return book_id in user_borrows

# ============= CORE FUNCTIONS =============

def load_users():
    """Load users from file"""
    users = {}
    try:
        if os.path.exists(USERS_FILE):
            with open(USERS_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        username, password, role = line.split("|")
                        users[username] = {"password": password, "role": role}
        if not users:
            users["admin"] = {"password": "admin123", "role": "admin"}
            save_users(users)
            print("✅ Default admin user created (username: admin, password: admin123)")
    except Exception as e:
        print(f"❌ Error loading users: {e}")
    return users

def save_users(users_dict):
    """Save users to file"""
    try:
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            for username, user_info in users_dict.items():
                f.write(f"{username}|{user_info['password']}|{user_info['role']}\n")
        return True
    except Exception as e:
        print(f"❌ Error saving users: {e}")
        return False

def save_to_file(books_dict, filename):
    """Save library data to text file"""
    try:
        with open(filename, "w", encoding="utf-8") as f:
            for book_id, book_info in books_dict.items():
                line = f"{book_id},{book_info['Title']},{book_info['Author']},{book_info['Year']},{book_info['TotalCopies']},{book_info['Available']},{book_info['Borrowed']}\n"
                f.write(line)
        return True
    except Exception as e:
        print(f"❌ Error saving data: {e}")
        return False

def load_from_file(filename):
    """Load library data from text file"""
    books = {}
    try:
        if os.path.exists(filename):
            with open(filename, "r", encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if line:
                        parts = line.split(",")
                        if len(parts) == 7:
                            book_id, title, author, year, total, available, borrowed = parts
                            books[book_id] = {
                                "Title": title,
                                "Author": author,
                                "Year": year,
                                "TotalCopies": int(total),
                                "Available": int(available),
                                "Borrowed": int(borrowed)
                            }
            print(f"✅ Loaded {len(books)} books from file")
        else:
            print("📝 No existing data file found. Starting with empty library.")
    except Exception as e:
        print(f"❌ Error loading data: {e}")
    return books

# ============= WEB DECORATORS =============

def login_required(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash('Please login first!', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash('Please login first!', 'error')
            return redirect(url_for('login'))
        if session.get('role') != 'admin':
            flash('Access denied! Admin role required.', 'error')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# ============= HTML TEMPLATES =============

BASE_HTML = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Library Management System</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        .navbar-brand { font-weight: bold; }
        .book-card { transition: transform 0.2s; }
        .book-card:hover { transform: translateY(-2px); }
        .stats-card { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }
        .available { color: #28a745; }
        .borrowed { color: #dc3545; }
        .my-borrowed { background-color: #fff3cd; border-left: 4px solid #ffc107; }
        .btn-group-sm > .btn { padding: 0.25rem 0.5rem; font-size: 0.875rem; }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container">
            <a class="navbar-brand" href="/dashboard">
                <i class="fas fa-book"></i> Library System
            </a>
            
            {% if session.username %}
            <div class="navbar-nav ms-auto">
                <span class="navbar-text me-3">
                    <i class="fas fa-user"></i> {{ session.username }} ({{ session.role }})
                </span>
                <a class="nav-link" href="/my-books">
                    <i class="fas fa-bookmark"></i> My Books
                </a>
                <a class="nav-link" href="/change-password">
                    <i class="fas fa-key"></i> Change Password
                </a>
                <a class="nav-link" href="/logout">
                    <i class="fas fa-sign-out-alt"></i> Logout
                </a>
            </div>
            {% endif %}
        </div>
    </nav>

    <div class="container mt-4">
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="alert alert-{{ 'danger' if category == 'error' else 'success' }} alert-dismissible fade show">
                        {{ message }}
                        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                    </div>
                {% endfor %}
            {% endif %}
        {% endwith %}

        {% block content %}{% endblock %}
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>'''

LOGIN_HTML = '''<div class="row justify-content-center">
    <div class="col-md-6">
        <div class="card">
            <div class="card-header">
                <h4 class="mb-0"><i class="fas fa-sign-in-alt"></i> User Login</h4>
            </div>
            <div class="card-body">
                <form method="POST">
                    <div class="mb-3">
                        <label for="username" class="form-label">Username</label>
                        <input type="text" class="form-control" id="username" name="username" required>
                    </div>
                    <div class="mb-3">
                        <label for="password" class="form-label">Password</label>
                        <input type="password" class="form-control" id="password" name="password" required>
                    </div>
                    <button type="submit" class="btn btn-primary w-100">Login</button>
                </form>
                <hr>
                <div class="text-center">
                    <p>Don't have an account? <a href="/register">Register here</a></p>
                    <p class="text-muted small">
                        <i class="fas fa-info-circle"></i> 
                        Default admin: username: admin, password: admin123
                    </p>
                </div>
            </div>
        </div>
    </div>
</div>'''

REGISTER_HTML = '''<div class="row justify-content-center">
    <div class="col-md-6">
        <div class="card">
            <div class="card-header">
                <h4 class="mb-0"><i class="fas fa-user-plus"></i> User Registration</h4>
            </div>
            <div class="card-body">
                <form method="POST">
                    <div class="mb-3">
                        <label for="username" class="form-label">Username</label>
                        <input type="text" class="form-control" id="username" name="username" required>
                    </div>
                    <div class="mb-3">
                        <label for="password" class="form-label">Password</label>
                        <input type="password" class="form-control" id="password" name="password" required>
                        <div class="form-text">Password must be at least 4 characters long.</div>
                    </div>
                    <div class="mb-3">
                        <label for="confirm_password" class="form-label">Confirm Password</label>
                        <input type="password" class="form-control" id="confirm_password" name="confirm_password" required>
                    </div>
                    <button type="submit" class="btn btn-success w-100">Register</button>
                </form>
                <hr>
                <div class="text-center">
                    <p>Already have an account? <a href="/login">Login here</a></p>
                </div>
            </div>
        </div>
    </div>
</div>'''

DASHBOARD_HTML = '''<div class="row mb-4">
    <div class="col-12">
        <h2><i class="fas fa-tachometer-alt"></i> Dashboard</h2>
        <p class="text-muted">Welcome back, {{ username }}!</p>
    </div>
</div>

<div class="row mb-4">
    <div class="col-md-3">
        <div class="card stats-card">
            <div class="card-body text-center">
                <h5 class="card-title"><i class="fas fa-book"></i> Total Books</h5>
                <h2 class="display-4">{{ total_books }}</h2>
            </div>
        </div>
    </div>
    <div class="col-md-3">
        <div class="card bg-success text-white">
            <div class="card-body text-center">
                <h5 class="card-title"><i class="fas fa-check-circle"></i> Available</h5>
                <h2 class="display-4">{{ total_available }}</h2>
            </div>
        </div>
    </div>
    <div class="col-md-3">
        <div class="card bg-warning text-white">
            <div class="card-body text-center">
                <h5 class="card-title"><i class="fas fa-users"></i> Borrowed</h5>
                <h2 class="display-4">{{ total_borrowed }}</h2>
            </div>
        </div>
    </div>
    <div class="col-md-3">
        <div class="card bg-info text-white">
            <div class="card-body text-center">
                <h5 class="card-title"><i class="fas fa-bookmark"></i> My Books</h5>
                <h2 class="display-4">{{ user_borrowed_count }}</h2>
            </div>
        </div>
    </div>
</div>

<div class="row">
    <div class="col-md-6">
        <div class="card">
            <div class="card-header">
                <h5 class="mb-0"><i class="fas fa-compass"></i> Quick Navigation</h5>
            </div>
            <div class="card-body">
                <div class="d-grid gap-2">
                    <a href="/books" class="btn btn-outline-primary">
                        <i class="fas fa-book-open"></i> View All Books
                    </a>
                    <a href="/books/available" class="btn btn-outline-success">
                        <i class="fas fa-check"></i> Available Books
                    </a>
                    <a href="/my-books" class="btn btn-outline-warning">
                        <i class="fas fa-bookmark"></i> My Borrowed Books
                    </a>
                    {% if role == 'admin' %}
                    <a href="/admin" class="btn btn-outline-danger">
                        <i class="fas fa-cog"></i> Admin Panel
                    </a>
                    {% endif %}
                </div>
            </div>
        </div>
    </div>
    
    <div class="col-md-6">
        <div class="card">
            <div class="card-header">
                <h5 class="mb-0"><i class="fas fa-info-circle"></i> System Info</h5>
            </div>
            <div class="card-body">
                <p><strong>Role:</strong> <span class="badge bg-{{ 'danger' if role == 'admin' else 'primary' }}">{{ role|title }}</span></p>
                <p><strong>Username:</strong> {{ username }}</p>
                <p><strong>My Borrowed Books:</strong> {{ user_borrowed_count }}</p>
                <p><strong>Access Level:</strong> 
                    {% if role == 'admin' %}
                        Full System Access
                    {% else %}
                        Book Browsing & Borrowing
                    {% endif %}
                </p>
            </div>
        </div>
    </div>
</div>'''

BOOKS_HTML = '''<div class="d-flex justify-content-between align-items-center mb-4">
    <h2>
        <i class="fas fa-book"></i> 
        {% if available_only %}Available Books{% else %}All Books{% endif %}
    </h2>
    
    <div class="d-flex gap-2">
        <form method="GET" class="d-flex">
            <input type="text" name="search" class="form-control me-2" placeholder="Search books..." value="{{ search_term }}">
            <button type="submit" class="btn btn-outline-primary">
                <i class="fas fa-search"></i>
            </button>
        </form>
        {% if not available_only %}
        <a href="/books/available" class="btn btn-success">
            <i class="fas fa-check"></i> Available Only
        </a>
        {% endif %}
        <a href="/my-books" class="btn btn-warning">
            <i class="fas fa-bookmark"></i> My Books
        </a>
        <a href="/books" class="btn btn-secondary">
            <i class="fas fa-redo"></i> Reset
        </a>
    </div>
</div>

{% if books %}
<div class="row">
    {% for book_id, book in books.items() %}
    <div class="col-md-6 col-lg-4 mb-4">
        <div class="card book-card h-100 {% if book_id in user_borrowed_ids %}my-borrowed{% endif %}">
            <div class="card-body">
                <h5 class="card-title">{{ book.Title }}</h5>
                <p class="card-text">
                    <strong>Author:</strong> {{ book.Author }}<br>
                    <strong>Year:</strong> {{ book.Year }}<br>
                    <strong>Book ID:</strong> <code>{{ book_id }}</code>
                </p>
                <div class="mb-3">
                    <span class="badge bg-{{ 'success' if book.Available > 0 else 'danger' }}">
                        {{ book.Available }}/{{ book.TotalCopies }} Available
                    </span>
                    {% if book_id in user_borrowed_ids %}
                    <span class="badge bg-warning mt-1">Borrowed by You</span>
                    {% endif %}
                </div>
            </div>
            <div class="card-footer">
                <div class="d-grid gap-2">
                    {% if book.Available > 0 and book_id not in user_borrowed_ids %}
                    <a href="/borrow/{{ book_id }}" class="btn btn-primary btn-sm">
                        <i class="fas fa-hand-holding"></i> Borrow
                    </a>
                    {% endif %}
                    {% if book_id in user_borrowed_ids %}
                    <a href="/return/{{ book_id }}" class="btn btn-warning btn-sm">
                        <i class="fas fa-undo"></i> Return
                    </a>
                    {% endif %}
                    {% if role == 'admin' %}
                    <a href="/admin/update-book/{{ book_id }}" class="btn btn-outline-secondary btn-sm">
                        <i class="fas fa-edit"></i> Edit
                    </a>
                    {% endif %}
                </div>
            </div>
        </div>
    </div>
    {% endfor %}
</div>
{% else %}
<div class="alert alert-info text-center">
    <h4><i class="fas fa-book-open"></i> No Books Found</h4>
    <p>{% if search_term %}No books match your search criteria.{% else %}The library is currently empty.{% endif %}</p>
</div>
{% endif %}'''

MY_BOOKS_HTML = '''<div class="row mb-4">
    <div class="col-12">
        <h2><i class="fas fa-bookmark"></i> My Borrowed Books</h2>
        <p class="text-muted">Books currently borrowed by you</p>
    </div>
</div>

{% if my_books %}
<div class="row">
    {% for book_id, book in my_books.items() %}
    <div class="col-md-6 col-lg-4 mb-4">
        <div class="card book-card h-100 my-borrowed">
            <div class="card-body">
                <h5 class="card-title">{{ book.Title }}</h5>
                <p class="card-text">
                    <strong>Author:</strong> {{ book.Author }}<br>
                    <strong>Year:</strong> {{ book.Year }}<br>
                    <strong>Book ID:</strong> <code>{{ book_id }}</code>
                </p>
                <div class="mb-3">
                    <span class="badge bg-warning">
                        <i class="fas fa-clock"></i> Borrowed by You
                    </span>
                </div>
            </div>
            <div class="card-footer">
                <div class="d-grid gap-2">
                    <a href="/return/{{ book_id }}" class="btn btn-warning btn-sm">
                        <i class="fas fa-undo"></i> Return Book
                    </a>
                    <a href="/books" class="btn btn-outline-primary btn-sm">
                        <i class="fas fa-search"></i> Browse More
                    </a>
                </div>
            </div>
        </div>
    </div>
    {% endfor %}
</div>
{% else %}
<div class="alert alert-info text-center">
    <h4><i class="fas fa-book-open"></i> No Books Borrowed</h4>
    <p>You haven't borrowed any books yet.</p>
    <a href="/books" class="btn btn-primary">Browse Books</a>
</div>
{% endif %}'''

ADMIN_HTML = '''<div class="row mb-4">
    <div class="col-12">
        <h2><i class="fas fa-cog"></i> Admin Control Panel</h2>
    </div>
</div>

<div class="row mb-4">
    <div class="col-md-3">
        <div class="card bg-primary text-white">
            <div class="card-body text-center">
                <h5><i class="fas fa-book"></i> Unique Books</h5>
                <h3>{{ total_books }}</h3>
            </div>
        </div>
    </div>
    <div class="col-md-3">
        <div class="card bg-info text-white">
            <div class="card-body text-center">
                <h5><i class="fas fa-copy"></i> Total Copies</h5>
                <h3>{{ total_copies }}</h3>
            </div>
        </div>
    </div>
    <div class="col-md-3">
        <div class="card bg-success text-white">
            <div class="card-body text-center">
                <h5><i class="fas fa-check"></i> Available</h5>
                <h3>{{ total_available }}</h3>
            </div>
        </div>
    </div>
    <div class="col-md-3">
        <div class="card bg-warning text-white">
            <div class="card-body text-center">
                <h5><i class="fas fa-users"></i> Borrowed</h5>
                <h3>{{ total_borrowed }}</h3>
            </div>
        </div>
    </div>
</div>

<div class="row">
    <div class="col-md-6">
        <div class="card">
            <div class="card-header">
                <h5 class="mb-0"><i class="fas fa-book-medical"></i> Book Management</h5>
            </div>
            <div class="card-body">
                <div class="d-grid gap-2">
                    <a href="/admin/add-book" class="btn btn-success">
                        <i class="fas fa-plus"></i> Add New Book
                    </a>
                    <a href="/books" class="btn btn-primary">
                        <i class="fas fa-eye"></i> View All Books
                    </a>
                    <a href="/admin/stats" class="btn btn-info">
                        <i class="fas fa-chart-bar"></i> Detailed Statistics
                    </a>
                </div>
            </div>
        </div>
    </div>
    
    <div class="col-md-6">
        <div class="card">
            <div class="card-header">
                <h5 class="mb-0"><i class="fas fa-users-cog"></i> User Management</h5>
            </div>
            <div class="card-body">
                <div class="d-grid gap-2">
                    <a href="/admin/users" class="btn btn-warning">
                        <i class="fas fa-user-friends"></i> View All Users
                    </a>
                    <a href="/admin/borrow-records" class="btn btn-secondary">
                        <i class="fas fa-history"></i> Borrow History
                    </a>
                    <div class="text-center mt-3">
                        <p class="mb-1"><strong>Total Users:</strong> {{ total_users }}</p>
                        <p class="mb-0 text-muted">User registration is open to public</p>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>'''

ADD_BOOK_HTML = '''<div class="row justify-content-center">
    <div class="col-md-8">
        <div class="card">
            <div class="card-header">
                <h4 class="mb-0"><i class="fas fa-plus-circle"></i> Add New Book</h4>
            </div>
            <div class="card-body">
                <form method="POST">
                    <div class="row">
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label for="book_id" class="form-label">Book ID *</label>
                                <input type="text" class="form-control" id="book_id" name="book_id" required>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label for="copies" class="form-label">Number of Copies *</label>
                                <input type="number" class="form-control" id="copies" name="copies" min="1" required>
                            </div>
                        </div>
                    </div>
                    
                    <div class="mb-3">
                        <label for="title" class="form-label">Book Title *</label>
                        <input type="text" class="form-control" id="title" name="title" required>
                    </div>
                    
                    <div class="row">
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label for="author" class="form-label">Author *</label>
                                <input type="text" class="form-control" id="author" name="author" required>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label for="year" class="form-label">Publication Year</label>
                                <input type="text" class="form-control" id="year" name="year">
                            </div>
                        </div>
                    </div>

                    <div class="alert alert-info">
                        <i class="fas fa-info-circle"></i> 
                        <strong>Note:</strong> If Book ID already exists, you can add additional copies below.
                    </div>

                    <div class="mb-3">
                        <label for="additional_copies" class="form-label">Additional Copies (for existing books)</label>
                        <input type="number" class="form-control" id="additional_copies" name="additional_copies" min="0" value="0">
                    </div>

                    <div class="d-grid gap-2">
                        <button type="submit" class="btn btn-success">
                            <i class="fas fa-save"></i> Save Book
                        </button>
                        <a href="/admin" class="btn btn-secondary">
                            <i class="fas fa-arrow-left"></i> Back to Admin Panel
                        </a>
                    </div>
                </form>
            </div>
        </div>
    </div>
</div>'''

UPDATE_BOOK_HTML = '''<div class="row justify-content-center">
    <div class="col-md-8">
        <div class="card">
            <div class="card-header">
                <h4 class="mb-0"><i class="fas fa-edit"></i> Update Book: {{ book_id }}</h4>
            </div>
            <div class="card-body">
                <form method="POST">
                    <div class="mb-3">
                        <label for="title" class="form-label">Book Title *</label>
                        <input type="text" class="form-control" id="title" name="title" value="{{ book.Title }}" required>
                    </div>
                    
                    <div class="row">
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label for="author" class="form-label">Author *</label>
                                <input type="text" class="form-control" id="author" name="author" value="{{ book.Author }}" required>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label for="year" class="form-label">Publication Year</label>
                                <input type="text" class="form-control" id="year" name="year" value="{{ book.Year }}">
                            </div>
                        </div>
                    </div>

                    <div class="mb-3">
                        <label for="total_copies" class="form-label">Total Copies *</label>
                        <input type="number" class="form-control" id="total_copies" name="total_copies" 
                               value="{{ book.TotalCopies }}" min="{{ book.Borrowed }}" required>
                        <div class="form-text">Cannot be less than currently borrowed copies ({{ book.Borrowed }})</div>
                    </div>

                    <div class="alert alert-warning">
                        <i class="fas fa-exclamation-triangle"></i> 
                        <strong>Current Status:</strong> 
                        {{ book.Available }} available, {{ book.Borrowed }} borrowed out of {{ book.TotalCopies }} total copies.
                    </div>

                    <div class="d-grid gap-2">
                        <button type="submit" class="btn btn-primary">
                            <i class="fas fa-save"></i> Update Book
                        </button>
                        <a href="/admin" class="btn btn-secondary">
                            <i class="fas fa-arrow-left"></i> Back to Admin Panel
                        </a>
                    </div>
                </form>
            </div>
        </div>
    </div>
</div>'''

USERS_HTML = '''<div class="d-flex justify-content-between align-items-center mb-4">
    <h2><i class="fas fa-user-friends"></i> All Registered Users</h2>
    <a href="/admin" class="btn btn-secondary">
        <i class="fas fa-arrow-left"></i> Back to Admin
    </a>
</div>

<div class="card">
    <div class="card-body">
        <div class="table-responsive">
            <table class="table table-striped">
                <thead>
                    <tr>
                        <th>Username</th>
                        <th>Role</th>
                        <th>Status</th>
                        <th>Borrowed Books</th>
                    </tr>
                </thead>
                <tbody>
                    {% for username, user_info in users.items() %}
                    <tr>
                        <td>
                            <i class="fas fa-user"></i> {{ username }}
                            {% if username == session.username %}
                            <span class="badge bg-info">You</span>
                            {% endif %}
                        </td>
                        <td>
                            <span class="badge bg-{{ 'danger' if user_info.role == 'admin' else 'primary' }}">
                                {{ user_info.role|title }}
                            </span>
                        </td>
                        <td>
                            <span class="badge bg-success">Active</span>
                        </td>
                        <td>
                            <span class="badge bg-warning">{{ get_user_borrowed_count(username) }}</span>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
</div>'''

STATS_HTML = '''<div class="d-flex justify-content-between align-items-center mb-4">
    <h2><i class="fas fa-chart-bar"></i> Detailed Library Statistics</h2>
    <a href="/admin" class="btn btn-secondary">
        <i class="fas fa-arrow-left"></i> Back to Admin
    </a>
</div>

<div class="row mb-4">
    <div class="col-md-3">
        <div class="card bg-primary text-white">
            <div class="card-body text-center">
                <h6>Unique Books</h6>
                <h3>{{ total_unique_books }}</h3>
            </div>
        </div>
    </div>
    <div class="col-md-3">
        <div class="card bg-info text-white">
            <div class="card-body text-center">
                <h6>Total Copies</h6>
                <h3>{{ total_all_copies }}</h3>
            </div>
        </div>
    </div>
    <div class="col-md-3">
        <div class="card bg-success text-white">
            <div class="card-body text-center">
                <h6>Available</h6>
                <h3>{{ total_available }}</h3>
            </div>
        </div>
    </div>
    <div class="col-md-3">
        <div class="card bg-warning text-white">
            <div class="card-body text-center">
                <h6>Borrowed</h6>
                <h3>{{ total_borrowed }}</h3>
            </div>
        </div>
    </div>
</div>

<div class="card">
    <div class="card-header">
        <h5 class="mb-0"><i class="fas fa-book"></i> Book-wise Breakdown</h5>
    </div>
    <div class="card-body">
        {% for book_id, book in books.items() %}
        <div class="mb-4 p-3 border rounded">
            <h6>{{ book.Title }} <small class="text-muted">by {{ book.Author }} ({{ book.Year }})</small></h6>
            <div class="row">
                <div class="col-md-6">
                    <p class="mb-1">Book ID: <code>{{ book_id }}</code></p>
                    <p class="mb-1">Total Copies: {{ book.TotalCopies }}</p>
                    <p class="mb-1">Available: <span class="available">{{ book.Available }}</span></p>
                    <p class="mb-0">Borrowed: <span class="borrowed">{{ book.Borrowed }}</span></p>
                </div>
                <div class="col-md-6">
                    {% if book.TotalCopies > 0 %}
                    {% set borrowed_pct = (book.Borrowed / book.TotalCopies) * 100 %}
                    <div class="progress mb-2" style="height: 20px;">
                        <div class="progress-bar bg-warning" style="width: {{ borrowed_pct }}%">
                            {{ "%.0f"|format(borrowed_pct) }}% Borrowed
                        </div>
                    </div>
                    <small class="text-muted">
                        Utilization: {{ "%.1f"|format(borrowed_pct) }}%
                    </small>
                    {% endif %}
                </div>
            </div>
        </div>
        {% endfor %}
    </div>
</div>'''

BORROW_HISTORY_HTML = '''<div class="d-flex justify-content-between align-items-center mb-4">
    <h2><i class="fas fa-history"></i> Borrow History</h2>
    <a href="/admin" class="btn btn-secondary">
        <i class="fas fa-arrow-left"></i> Back to Admin
    </a>
</div>

<div class="card">
    <div class="card-body">
        <div class="table-responsive">
            <table class="table table-striped">
                <thead>
                    <tr>
                        <th>Username</th>
                        <th>Book ID</th>
                        <th>Book Title</th>
                        <th>Borrow Date</th>
                        <th>Return Date</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    {% for record in borrow_history %}
                    <tr>
                        <td>{{ record.username }}</td>
                        <td><code>{{ record.book_id }}</code></td>
                        <td>{{ record.book_title }}</td>
                        <td>{{ record.borrow_date }}</td>
                        <td>{{ record.return_date if record.return_date else 'Not returned' }}</td>
                        <td>
                            <span class="badge bg-{{ 'success' if record.return_date else 'warning' }}">
                                {{ 'Returned' if record.return_date else 'Borrowed' }}
                            </span>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
</div>'''

CHANGE_PASSWORD_HTML = '''<div class="row justify-content-center">
    <div class="col-md-6">
        <div class="card">
            <div class="card-header">
                <h4 class="mb-0"><i class="fas fa-key"></i> Change Password</h4>
            </div>
            <div class="card-body">
                <form method="POST">
                    <div class="mb-3">
                        <label for="current_password" class="form-label">Current Password</label>
                        <input type="password" class="form-control" id="current_password" name="current_password" required>
                    </div>
                    <div class="mb-3">
                        <label for="new_password" class="form-label">New Password</label>
                        <input type="password" class="form-control" id="new_password" name="new_password" required>
                        <div class="form-text">Password must be at least 4 characters long.</div>
                    </div>
                    <div class="mb-3">
                        <label for="confirm_password" class="form-label">Confirm New Password</label>
                        <input type="password" class="form-control" id="confirm_password" name="confirm_password" required>
                    </div>
                    <div class="d-grid gap-2">
                        <button type="submit" class="btn btn-primary">Change Password</button>
                        <a href="/dashboard" class="btn btn-secondary">Cancel</a>
                    </div>
                </form>
            </div>
        </div>
    </div>
</div>'''

# ============= WEB ROUTES =============

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        # Agar koi form / par submit kare toh usko login route par redirect karein
        return redirect(url_for('login'))
    
    if 'username' in session:
        return redirect(url_for('dashboard'))
    return render_template_string(BASE_HTML.replace('{% block content %}{% endblock %}', LOGIN_HTML))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        users = load_users()
        if username in users and users[username]['password'] == password:
            session['username'] = username
            session['role'] = users[username]['role']
            flash(f'Login successful! Welcome {username}', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password!', 'error')
    
    # GET request - show login page
    return render_template_string(BASE_HTML.replace('{% block content %}{% endblock %}', LOGIN_HTML))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        users = load_users()
        
        if not username:
            flash('Username cannot be empty!', 'error')
        elif username in users:
            flash('Username already exists!', 'error')
        elif password != confirm_password:
            flash('Passwords do not match!', 'error')
        elif len(password) < 4:
            flash('Password must be at least 4 characters!', 'error')
        else:
            users[username] = {"password": password, "role": "member"}
            save_users(users)
            flash('Registration successful! You can now login.', 'success')
            return redirect(url_for('login'))
    
    # GET request - show registration page
    return render_template_string(BASE_HTML.replace('{% block content %}{% endblock %}', REGISTER_HTML))

@app.route('/dashboard')
@login_required
def dashboard():
    books = load_from_file(BOOKS_FILE)
    total_books = len(books)
    total_available = sum(book['Available'] for book in books.values())
    total_borrowed = sum(book['Borrowed'] for book in books.values())
    user_borrowed_count = len(get_user_borrowed_books(session['username']))
    
    return render_template_string(
        BASE_HTML.replace('{% block content %}{% endblock %}', DASHBOARD_HTML),
        username=session['username'],
        role=session['role'],
        total_books=total_books,
        total_available=total_available,
        total_borrowed=total_borrowed,
        user_borrowed_count=user_borrowed_count
    )

@app.route('/my-books')
@login_required
def my_books():
    books = load_from_file(BOOKS_FILE)
    user_borrowed_ids = get_user_borrowed_books(session['username'])
    
    my_books = {}
    for book_id in user_borrowed_ids:
        if book_id in books:
            my_books[book_id] = books[book_id]
    
    return render_template_string(
        BASE_HTML.replace('{% block content %}{% endblock %}', MY_BOOKS_HTML),
        my_books=my_books
    )

@app.route('/books')
@login_required
def view_books():
    books = load_from_file(BOOKS_FILE)
    search_term = request.args.get('search', '')
    
    if search_term:
        filtered_books = {}
        for book_id, book in books.items():
            if (search_term.lower() in book['Title'].lower() or 
                search_term.lower() in book['Author'].lower()):
                filtered_books[book_id] = book
        books = filtered_books
    
    user_borrowed_ids = get_user_borrowed_books(session['username'])
    
    return render_template_string(
        BASE_HTML.replace('{% block content %}{% endblock %}', BOOKS_HTML),
        books=books, 
        search_term=search_term,
        role=session['role'],
        user_borrowed_ids=user_borrowed_ids
    )

@app.route('/books/available')
@login_required
def available_books():
    books = load_from_file(BOOKS_FILE)
    available_books = {id: book for id, book in books.items() if book['Available'] > 0}
    user_borrowed_ids = get_user_borrowed_books(session['username'])
    
    return render_template_string(
        BASE_HTML.replace('{% block content %}{% endblock %}', BOOKS_HTML),
        books=available_books, 
        available_only=True,
        role=session['role'],
        user_borrowed_ids=user_borrowed_ids
    )

@app.route('/borrow/<book_id>')
@login_required
def borrow_book(book_id):
    books = load_from_file(BOOKS_FILE)
    username = session['username']
    
    if book_id in books:
        book = books[book_id]
        
        if book["Available"] > 0:
            if is_book_borrowed_by_user(username, book_id):
                flash(f'You have already borrowed "{book["Title"]}"!', 'error')
                return redirect(url_for('view_books'))
            
            book["Available"] -= 1
            book["Borrowed"] += 1
            
            if borrow_book_for_user(username, book_id):
                if save_to_file(books, BOOKS_FILE):
                    flash(f'You have borrowed "{book["Title"]}" successfully!', 'success')
                else:
                    flash('Error saving data!', 'error')
            else:
                flash('Error recording borrow!', 'error')
        else:
            flash(f'Sorry, all copies of "{book["Title"]}" are borrowed.', 'error')
    else:
        flash('Book not found!', 'error')
    
    return redirect(url_for('view_books'))

@app.route('/return/<book_id>')
@login_required
def return_book(book_id):
    books = load_from_file(BOOKS_FILE)
    username = session['username']
    
    if book_id in books:
        book = books[book_id]
        
        if is_book_borrowed_by_user(username, book_id):
            book["Available"] += 1
            book["Borrowed"] -= 1
            
            if return_book_for_user(username, book_id):
                if save_to_file(books, BOOKS_FILE):
                    flash(f'"{book["Title"]}" returned successfully!', 'success')
                else:
                    flash('Error saving data!', 'error')
            else:
                flash('Error recording return!', 'error')
        else:
            flash('You cannot return this book as you have not borrowed it!', 'error')
    else:
        flash('Book not found!', 'error')
    
    return redirect(url_for('view_books'))

@app.route('/admin')
@admin_required
def admin_panel():
    books = load_from_file(BOOKS_FILE)
    users = load_users()
    
    total_unique_books = len(books)
    total_all_copies = sum(book['TotalCopies'] for book in books.values())
    total_available = sum(book['Available'] for book in books.values())
    total_borrowed = sum(book['Borrowed'] for book in books.values())
    
    return render_template_string(
        BASE_HTML.replace('{% block content %}{% endblock %}', ADMIN_HTML),
        total_books=total_unique_books,
        total_copies=total_all_copies,
        total_available=total_available,
        total_borrowed=total_borrowed,
        total_users=len(users)
    )

@app.route('/admin/add-book', methods=['GET', 'POST'])
@admin_required
def add_book():
    books = load_from_file(BOOKS_FILE)
    
    if request.method == 'POST':
        book_id = request.form['book_id']
        book_name = request.form['title']
        author_name = request.form['author']
        year_published = request.form['year']
        
        try:
            total_copies = int(request.form['copies'])
            if total_copies <= 0:
                flash('Number of copies must be positive!', 'error')
                return redirect(url_for('add_book'))
        except ValueError:
            flash('Invalid number for copies!', 'error')
            return redirect(url_for('add_book'))
        
        if book_id in books:
            try:
                copies = int(request.form.get('additional_copies', 0))
                if copies > 0:
                    books[book_id]['TotalCopies'] += copies
                    books[book_id]['Available'] += copies
                    if save_to_file(books, BOOKS_FILE):
                        flash(f'Added {copies} copies to existing book!', 'success')
                else:
                    flash('No additional copies added.', 'info')
            except ValueError:
                flash('Invalid number for additional copies!', 'error')
        else:
            books[book_id] = {
                "Title": book_name,
                "Author": author_name,
                "Year": year_published,
                "TotalCopies": total_copies,
                "Available": total_copies,
                "Borrowed": 0
            }
            if save_to_file(books, BOOKS_FILE):
                flash('Book added successfully!', 'success')
        
        return redirect(url_for('admin_panel'))
    
    return render_template_string(BASE_HTML.replace('{% block content %}{% endblock %}', ADD_BOOK_HTML), books=books)

@app.route('/admin/update-book/<book_id>', methods=['GET', 'POST'])
@admin_required
def update_book(book_id):
    books = load_from_file(BOOKS_FILE)
    
    if book_id not in books:
        flash('Book not found!', 'error')
        return redirect(url_for('admin_panel'))
    
    book = books[book_id]
    
    if request.method == 'POST':
        book['Title'] = request.form['title']
        book['Author'] = request.form['author']
        book['Year'] = request.form['year']
        
        try:
            new_copies = int(request.form['total_copies'])
            if new_copies >= book['Borrowed']:
                book['Available'] = new_copies - book['Borrowed']
                book['TotalCopies'] = new_copies
            else:
                flash('Total copies cannot be less than borrowed copies!', 'error')
                return redirect(url_for('update_book', book_id=book_id))
        except ValueError:
            flash('Invalid number for copies!', 'error')
            return redirect(url_for('update_book', book_id=book_id))
        
        if save_to_file(books, BOOKS_FILE):
            flash('Book updated successfully!', 'success')
        return redirect(url_for('admin_panel'))
    
    return render_template_string(
        BASE_HTML.replace('{% block content %}{% endblock %}', UPDATE_BOOK_HTML),
        book_id=book_id, 
        book=book
    )

@app.route('/admin/delete-book/<book_id>')
@admin_required
def delete_book(book_id):
    books = load_from_file(BOOKS_FILE)
    
    if book_id in books:
        book = books[book_id]
        if book['Borrowed'] > 0:
            flash(f'Cannot delete book! {book["Borrowed"]} copies are currently borrowed.', 'error')
        else:
            del books[book_id]
            if save_to_file(books, BOOKS_FILE):
                flash('Book deleted successfully!', 'success')
    else:
        flash('Book not found!', 'error')
    
    return redirect(url_for('admin_panel'))

@app.route('/admin/users')
@admin_required
def view_users():
    users = load_users()
    
    def get_user_borrowed_count(username):
        return len(get_user_borrowed_books(username))
    
    return render_template_string(
        BASE_HTML.replace('{% block content %}{% endblock %}', USERS_HTML),
        users=users,
        get_user_borrowed_count=get_user_borrowed_count
    )

@app.route('/admin/stats')
@admin_required
def library_stats():
    books = load_from_file(BOOKS_FILE)
    total_unique_books = len(books)
    total_all_copies = sum(book['TotalCopies'] for book in books.values())
    total_available = sum(book['Available'] for book in books.values())
    total_borrowed = sum(book['Borrowed'] for book in books.values())
    
    return render_template_string(
        BASE_HTML.replace('{% block content %}{% endblock %}', STATS_HTML),
        books=books,
        total_unique_books=total_unique_books,
        total_all_copies=total_all_copies,
        total_available=total_available,
        total_borrowed=total_borrowed
    )

@app.route('/admin/borrow-records')
@admin_required
def borrow_history():
    borrows = load_borrows()
    books = load_from_file(BOOKS_FILE)
    
    history = []
    for username, user_borrows in borrows.items():
        for borrow in user_borrows:
            book_title = books.get(borrow['book_id'], {}).get('Title', 'Unknown Book')
            history.append({
                'username': username,
                'book_id': borrow['book_id'],
                'book_title': book_title,
                'borrow_date': borrow['borrow_date'],
                'return_date': borrow['return_date']
            })
    
    # Sort by borrow date (newest first)
    history.sort(key=lambda x: x['borrow_date'], reverse=True)
    
    return render_template_string(
        BASE_HTML.replace('{% block content %}{% endblock %}', BORROW_HISTORY_HTML),
        borrow_history=history
    )

@app.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_password = request.form['current_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']
        
        users = load_users()
        username = session['username']
        
        if users[username]['password'] != current_password:
            flash('Current password is incorrect!', 'error')
        elif new_password != confirm_password:
            flash('New passwords do not match!', 'error')
        elif len(new_password) < 4:
            flash('Password must be at least 4 characters!', 'error')
        else:
            users[username]['password'] = new_password
            save_users(users)
            flash('Password changed successfully!', 'success')
            return redirect(url_for('dashboard'))
    
    return render_template_string(BASE_HTML.replace('{% block content %}{% endblock %}', CHANGE_PASSWORD_HTML))

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully!', 'info')
    return redirect(url_for('login'))

if __name__ == '__main__':
    print("📚 Library Management System - Web Version")
    print("🌐 Starting web server...")
    print("📍 Access the application at: http://localhost:5000")
    print("🔐 Default admin login: username: admin, password: admin123")
    print("🆕 NEW: User-specific borrow tracking enabled!")
    print("📖 3 Files will be created:")
    print("   - library_users.txt (User accounts)")
    print("   - library_books.txt (Book inventory)") 
    print("   - library_borrows.txt (Borrow tracking)")
    app.run(debug=True, host='0.0.0.0', port=5000)