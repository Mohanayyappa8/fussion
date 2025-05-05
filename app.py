from flask import Flask, render_template, request, redirect, session, url_for, jsonify, flash
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import date
from dotenv import load_dotenv
from init_db import create_all_tables

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "fallbacksecret")

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

DB_URL = os.getenv("DB_URL")

def restaurant_db():
    conn = psycopg2.connect(DB_URL, cursor_factory=RealDictCursor)
    return conn

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def ensure_admin_table():
    conn = restaurant_db()
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS admin_users (
        id SERIAL PRIMARY KEY,
        username VARCHAR(100) UNIQUE NOT NULL,
        password_hash TEXT NOT NULL)''')
    conn.commit()
    cursor.close()
    conn.close()

def add_column_if_missing():
    conn = restaurant_db()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT special_request FROM reservations LIMIT 1")
    except Exception:
        cursor.execute("ALTER TABLE reservations ADD COLUMN special_request TEXT")
        conn.commit()
    cursor.close()
    conn.close()

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
        conn = restaurant_db()
        cursor = conn.cursor()
        try:
            cursor.execute('INSERT INTO admin_users (username, password_hash) VALUES (%s, %s)', (username, hashed))
            conn.commit()
        except:
            return 'Username already exists!'
        finally:
            cursor.close()
            conn.close()
        return redirect('/admin/login')
    return render_template('register.html')

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    ensure_admin_table()
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = restaurant_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM admin_users WHERE username = %s', (username,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
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
    conn = restaurant_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM reservations WHERE reservation_date < %s", (today,))
    conn.commit()
    cursor.execute('SELECT COUNT(*) FROM reservations')
    booking_count = cursor.fetchone()['count']
    cursor.execute('''SELECT name, reservation_date, reservation_time, number_of_guests, special_request FROM reservations
        WHERE reservation_date = %s ORDER BY reservation_time ASC''', (today,))
    todays_guests = cursor.fetchall()
    cursor.execute('''SELECT name, reservation_date, reservation_time, number_of_guests, special_request FROM reservations
        WHERE reservation_date > %s ORDER BY reservation_date ASC, reservation_time ASC''', (today,))
    upcoming_guests = cursor.fetchall()
    cursor.close()
    conn.close()
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
    return jsonify(dishes)

@app.route('/api/menu')
def get_menu():
    conn = restaurant_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM menu_items')
    menu = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(menu)

@app.route('/reservations', methods=['GET', 'POST'])
def reservations():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        reservation_date = request.form['date']
        reservation_time = request.form['time']
        number_of_guests = request.form['guests']
        special_request = request.form.get('special_request', 'None')
        conn = restaurant_db()
        cursor = conn.cursor()
        cursor.execute('''INSERT INTO reservations (name, email, phone, reservation_date, reservation_time, number_of_guests, special_request)
            VALUES (%s, %s, %s, %s, %s, %s, %s)''', (name, email, phone, reservation_date, reservation_time, number_of_guests, special_request))
        conn.commit()
        cursor.close()
        conn.close()
        flash('🎉 Reservation confirmed! See you soon at Fusion Affair!')
        return redirect('/')
    return render_template('reservations.html')

@app.route('/admin/menu')
def admin_menu():
    if 'admin_user' not in session:
        return redirect('/admin/login')
    conn = restaurant_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM menu_items')
    menu_items = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('admin_menu.html', menu_items=menu_items)

@app.route('/admin/signature')
def admin_signature():
    if 'admin_user' not in session:
        return redirect('/admin/login')
    conn = restaurant_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM signature_dishes')
    signature_dishes = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('admin_signature.html', signature_dishes=signature_dishes)

@app.route('/admin/fusion-vibe')
def admin_fusion_vibe():
    if 'admin_user' not in session:
        return redirect('/admin/login')
    conn = restaurant_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM fusion_vibe')
    vibe_items = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('admin_fusion_vibe.html', fusion_items=vibe_items)

@app.route('/admin/gallery')
def admin_gallery():
    if 'admin_user' not in session:
        return redirect('/admin/login')
    conn = restaurant_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM gallery')
    gallery_items = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('admin_gallery.html', gallery_items=gallery_items)

# Call setup functions
create_all_tables()
ensure_admin_table()
add_column_if_missing()

if __name__ == '__main__':
    app.run(debug=True)
