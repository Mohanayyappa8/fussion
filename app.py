from flask import Flask, render_template, request, redirect, session, url_for, jsonify, flash
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import date
from init_db import create_all_tables
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "fallbacksecret")

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def restaurant_db():
    db_name = os.getenv("DB_NAME", "restaurant.db")
    conn = sqlite3.connect(db_name)
    conn.row_factory = sqlite3.Row
    return conn

def add_column_if_missing():
    conn = restaurant_db()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT special_request FROM reservations LIMIT 1")
    except sqlite3.OperationalError:
        try:
            cursor.execute("ALTER TABLE reservations ADD COLUMN special_request TEXT")
            print("✅ 'special_request' column added to reservations table.")
        except Exception as e:
            print(f"❌ Failed to add column: {e}")
    cursor.close()
    conn.close()


def ensure_admin_table():
    db = restaurant_db()
    cursor = db.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS admin_users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL)''')
    db.commit()
    cursor.close()
    db.close()


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Ensure admin_users table exists
admin_table_created = False
def ensure_admin_table():
    global admin_table_created
    if not admin_table_created:
        db = restaurant_db()
        cursor = db.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS admin_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL)''')
        db.commit()
        cursor.close()
        db.close()
        admin_table_created = True

@app.route('/admin/register', methods=['GET', 'POST'])
def admin_register():
    ensure_admin_table()
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm = request.form['confirm_password']
        if password != confirm:
            return 'Passwords do not match!'
        hashed = generate_password_hash(password)
        db = restaurant_db()
        cursor = db.cursor()
        try:
            cursor.execute('INSERT INTO admin_users (username, password_hash) VALUES (?, ?)', (username, hashed))
            db.commit()
        except sqlite3.IntegrityError:
            return 'Username already exists!'
        finally:
            cursor.close()
            db.close()
        return redirect('/admin/login')
    return render_template('register.html')

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    ensure_admin_table()
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = restaurant_db()
        cursor = db.cursor()
        cursor.execute('SELECT * FROM admin_users WHERE username = ?', (username,))
        user = cursor.fetchone()
        cursor.close()
        db.close()
        if user and check_password_hash(user['password_hash'], password):
            session['admin_user'] = username
            return redirect('/admin/dashboard')
        else:
            return 'Invalid credentials!'
    return render_template('login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_user', None)
    return redirect('/admin/login')

@app.route('/admin/dashboard')
def admin_dashboard():
    if 'admin_user' not in session:
        return redirect('/admin/login')
    today = date.today()
    db = restaurant_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM reservations WHERE DATE(reservation_date) < ?", (today,))
    db.commit()
    cursor.execute('SELECT COUNT(*) AS total FROM reservations')
    booking_count = cursor.fetchone()['total']
    cursor.execute('''SELECT name, reservation_date, reservation_time, number_of_guests, special_request FROM reservations
        WHERE DATE(reservation_date) = ? ORDER BY reservation_time ASC''', (today,))
    todays_guests = cursor.fetchall()
    cursor.execute('''SELECT name, reservation_date, reservation_time, number_of_guests, special_request FROM reservations
        WHERE DATE(reservation_date) > ? ORDER BY reservation_date ASC, reservation_time ASC''', (today,))
    upcoming_guests = cursor.fetchall()
    cursor.close()
    db.close()
    return render_template('dashboard.html', admin_user=session['admin_user'], booking_count=booking_count,
        todays_guests=todays_guests, upcoming_guests=upcoming_guests,
        admin_controls={
            'Manage Menu Items': '/admin/menu',
            'Manage Signature Dishes': '/admin/signature',
            'Manage Vibe': '/admin/fusion-vibe',
            'Manage Gallery': '/admin/gallery',
            'Logout': '/admin/logout'})

@app.route('/')
def index():
    ensure_admin_table()
    conn = restaurant_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM menu_items')
    menu_items = cursor.fetchall()
    cursor.execute('SELECT * FROM fusion_vibe')
    vibe_items = cursor.fetchall()
    cursor.execute('SELECT * FROM gallery')
    gallery_items = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('index.html', menu_items=menu_items, vibe_items=vibe_items, gallery_items=gallery_items)

@app.route('/api/signature-dishes')
def get_signature_dishes():
    conn = restaurant_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM signature_dishes')
    dishes = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify([dict(d) for d in dishes])

@app.route('/api/menu')
def get_menu():
    conn = restaurant_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM menu_items')
    menu = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify([dict(m) for m in menu])

@app.route('/reservations', methods=['GET', 'POST'])
def reservations():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        reservation_date = request.form['date']
        reservation_time = request.form['time']
        number_of_guests = request.form['guests']
        conn = restaurant_db()
        cursor = conn.cursor()
        cursor.execute('''INSERT INTO reservations (name, email, phone, reservation_date, reservation_time, number_of_guests,special_request)
            VALUES (?, ?, ?, ?, ?, ?,?)''', (name, email, phone, reservation_date, reservation_time, number_of_guests, special_request))
        conn.commit()
        cursor.close()
        conn.close()
        flash('🎉 Reservation confirmed! See you soon at Fusion Affair!')
        return redirect('/')
    return render_template('reservations.html')

@app.route('/admin/menu', methods=['GET'])
def admin_menu():
    if 'admin_user' not in session:
        return redirect('/admin/login')
    db = restaurant_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM menu_items')
    menu_items = cursor.fetchall()
    cursor.close()
    db.close()
    return render_template('admin_menu.html', menu_items=menu_items)

@app.route('/admin/signature', methods=['GET'])
def admin_signature():
    if 'admin_user' not in session:
        return redirect('/admin/login')
    db = restaurant_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM signature_dishes')
    signature_dishes = cursor.fetchall()
    cursor.close()
    db.close()
    return render_template('admin_signature.html', signature_dishes=signature_dishes)

@app.route('/admin/fusion-vibe', methods=['GET'])
def admin_fusion_vibe():
    if 'admin_user' not in session:
        return redirect('/admin/login')
    db = restaurant_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM fusion_vibe')
    vibe_items = cursor.fetchall()
    cursor.close()
    db.close()
    return render_template('admin_fusion_vibe.html', fusion_items=vibe_items)

@app.route('/admin/gallery', methods=['GET'])
def admin_gallery():
    if 'admin_user' not in session:
        return redirect('/admin/login')
    db = restaurant_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM gallery')
    gallery_items = cursor.fetchall()
    cursor.close()
    db.close()
    return render_template('admin_gallery.html', gallery_items=gallery_items)



create_all_tables()
ensure_admin_table()
add_column_if_missing()


if __name__ == '__main__':
    app.run(debug=True)


