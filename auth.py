import sqlite3
import bcrypt

import os
DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../database/users.db"))


def create_users_table():
    """Creates the users table if it doesn't exist."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        first_name TEXT NOT NULL,
                        last_name TEXT NOT NULL,
                        email TEXT UNIQUE NOT NULL,
                        password TEXT NOT NULL)''')
    conn.commit()
    conn.close()

def register_user(first_name, last_name, email, password):
    """Registers a new user with an encrypted password."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    try:
        cursor.execute("INSERT INTO users (first_name, last_name, email, password) VALUES (?, ?, ?, ?)", 
                       (first_name, last_name, email, hashed_password))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False  # Email already exists

def login_user(email, password):
    """Checks login credentials."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT password FROM users WHERE email = ?", (email,))
    result = cursor.fetchone()
    conn.close()

    if result and bcrypt.checkpw(password.encode('utf-8'), result[0]):
        return True  # Login successful
    return False  # Login failed

# Create table if not exists
create_users_table()
