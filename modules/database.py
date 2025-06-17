
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

DB_NAME = 'medical_db.db'

def get_faqs():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT question, answer FROM faq")
    faqs = cursor.fetchall()
    conn.close()
    return faqs

def get_emergency():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT disease_type, instructions FROM emergency_info")
    emergency = cursor.fetchall()
    conn.close()
    return emergency



# Add a new user for registration
def add_user(name, email, password, contact, gender):
    hashed_password = generate_password_hash(password) 
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO userbase (name, email, password, contact_info, gender)
        VALUES (?, ?, ?, ?, ?)
    ''', (name, email, hashed_password, contact, gender))
    conn.commit()
    conn.close()

# Check if the user exists  for login
def check_user(email, password):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT userid, name, email, password FROM userbase WHERE email = ?', (email,))
    user = cursor.fetchone()
    conn.close()
    
    if user and check_password_hash(user[3], password): 
        return user 
    return None

def get_user_by_id(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT userid, name, email, contact_info, gender FROM userbase WHERE userid = ?', (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user

