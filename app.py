from flask import Flask, render_template, request, redirect, session, url_for, jsonify, flash
import psycopg2
import os
from psycopg2.extras import RealDictCursor
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import date
from init_db import create_all_tables
from dotenv import load_dotenv
load_dotenv()


from init_db import create_all_tables
create_all_tables()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "fallbacksecret")

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

DB_URL = os.getenv("DATABASE_URL")

def restaurant_db():
    conn = psycopg2.connect(DB_URL)
    return conn

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/admin/register', methods=['GET', 'POST'])
def admin_register():
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
            cursor.execute('INSERT INTO admin_users (username, password_hash) VALUES (%s, %s)', (username, hashed))
            db.commit()
        except psycopg2.errors.UniqueViolation:
            db.rollback()
            return 'Username already exists!'
        finally:
            cursor.close()
            db.close()
        return redirect('/admin/login')
    return render_template('register.html')

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = restaurant_db()
        cursor = db.cursor()
        cursor.execute('SELECT * FROM admin_users WHERE username = %s', (username,))
        user = cursor.fetchone()
        cursor.close()
        db.close()
        if user and check_password_hash(user[2], password):
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
    cursor.execute("DELETE FROM reservations WHERE reservation_date < %s", (today,))
    db.commit()
    cursor.execute('SELECT COUNT(*) FROM reservations')
    booking_count = cursor.fetchone()[0]
    cursor.execute('''SELECT name, reservation_date, reservation_time, number_of_guests, special_request FROM reservations
        WHERE reservation_date = %s ORDER BY reservation_time ASC''', (today,))
    todays_guests = cursor.fetchall()
    cursor.execute('''SELECT name, reservation_date, reservation_time, number_of_guests, special_request FROM reservations
        WHERE reservation_date > %s ORDER BY reservation_date ASC, reservation_time ASC''', (today,))
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
    result = [dict(zip([desc[0] for desc in cursor.description], row)) for row in dishes]
    cursor.close()
    conn.close()
    return jsonify(result)

@app.route('/api/menu')
def get_menu():
    conn = restaurant_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM menu_items')
    menu = cursor.fetchall()
    result = [dict(zip([desc[0] for desc in cursor.description], row)) for row in menu]
    cursor.close()
    conn.close()
    return jsonify(result)

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

# ------------------ ADMIN: MENU ITEMS ------------------
@app.route('/admin/menu', methods=['GET', 'POST'])
def admin_menu():
    if 'admin_user' not in session:
        return redirect('/admin/login')

    db = restaurant_db()
    cursor = db.cursor()
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        price = request.form['price']
        image_url = request.form['image_url']
        cursor.execute("INSERT INTO menu_items (name, description, price, image_url) VALUES (%s, %s, %s, %s)",
                       (name, description, price, image_url))
        db.commit()
    cursor.execute("SELECT * FROM menu_items")
    menu_items = cursor.fetchall()
    cursor.close()
    db.close()
    return render_template('admin_menu.html', menu_items=menu_items)

# ------------------ ADMIN: SIGNATURE DISHES ------------------
@app.route('/admin/signature', methods=['GET', 'POST'])
def admin_signature():
    if 'admin_user' not in session:
        return redirect('/admin/login')

    db = restaurant_db()
    cursor = db.cursor()
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        image_url = request.form['image_url']
        cursor.execute("INSERT INTO signature_dishes (name, description, image_url) VALUES (%s, %s, %s)",
                       (name, description, image_url))
        db.commit()
    cursor.execute("SELECT * FROM signature_dishes")
    signature_items = cursor.fetchall()
    cursor.close()
    db.close()
    return render_template('admin_signature.html', signature_items=signature_items)

# ------------------ ADMIN: FUSION VIBE ------------------
@app.route('/admin/fusion-vibe', methods=['GET', 'POST'])
def admin_fusion_vibe():
    if 'admin_user' not in session:
        return redirect('/admin/login')

    db = restaurant_db()
    cursor = db.cursor()
    if request.method == 'POST':
        image_url = request.form['image_url']
        cursor.execute("INSERT INTO fusion_vibe (image_url) VALUES (%s)", (image_url,))
        db.commit()
    cursor.execute("SELECT * FROM fusion_vibe")
    fusion_items = cursor.fetchall()
    cursor.close()
    db.close()
    return render_template('admin_fusion_vibe.html', fusion_items=fusion_items)

# ------------------ ADMIN: GALLERY ------------------
@app.route('/admin/gallery', methods=['GET', 'POST'])
def admin_gallery():
    if 'admin_user' not in session:
        return redirect('/admin/login')

    db = restaurant_db()
    cursor = db.cursor()
    if request.method == 'POST':
        image_url = request.form['image_url']
        cursor.execute("INSERT INTO gallery (image_url) VALUES (%s)", (image_url,))
        db.commit()
    cursor.execute("SELECT * FROM gallery")
    gallery_items = cursor.fetchall()
    cursor.close()
    db.close()
    return render_template('admin_gallery.html', gallery_items=gallery_items)



create_all_tables()

if __name__ == '__main__':
    app.run(debug=True)
