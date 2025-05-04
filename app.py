from flask import Flask, render_template, request, redirect, session, url_for, jsonify, flash
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # use env var in production

# MySQL connection
def restaurant_db():
    return mysql.connector.connect(
        host='127.0.0.1',
        port=3307,
        user="root",
        password="Mass8187879186",
        database="restaurant_db"
    )

# Ensure admin_users table exists (run on homepage access)
admin_table_created = False
def ensure_admin_table():
    global admin_table_created
    if not admin_table_created:
        db = restaurant_db()
        cursor = db.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS admin_users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(100) UNIQUE NOT NULL,
                password_hash TEXT NOT NULL
            )
        ''')
        db.commit()
        cursor.close()
        db.close()
        admin_table_created = True

# Admin Register
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
            cursor.execute('INSERT INTO admin_users (username, password_hash) VALUES (%s, %s)', (username, hashed))
            db.commit()
        except mysql.connector.errors.IntegrityError:
            return 'Username already exists!'
        finally:
            cursor.close()
            db.close()

        return redirect('/admin/login')

    return render_template('register.html')

# Admin Login
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    ensure_admin_table()
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        db = restaurant_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute('SELECT * FROM admin_users WHERE username = %s', (username,))
        user = cursor.fetchone()
        cursor.close()
        db.close()

        if user and check_password_hash(user['password_hash'], password):
            session['admin_user'] = username
            return redirect('/admin/dashboard')
        else:
            return 'Invalid credentials!'

    return render_template('login.html')

#from datetime import date
from datetime import date
from datetime import date

@app.route('/admin/dashboard')
def admin_dashboard():
    if 'admin_user' not in session:
        return redirect('/admin/login')

    today = date.today()

    db = restaurant_db()
    cursor = db.cursor(dictionary=True)

    # Delete old reservations (before today only)
    cursor.execute("DELETE FROM reservations WHERE DATE(reservation_date) < %s", (today,))
    db.commit()

    # Count total reservations
    cursor.execute('SELECT COUNT(*) AS total FROM reservations')
    booking_count = cursor.fetchone()['total']

    # Fetch today's reservations
    cursor.execute('''
        SELECT name, reservation_date, reservation_time, number_of_guests
        FROM reservations
        WHERE DATE(reservation_date) = %s
        ORDER BY reservation_time ASC
    ''', (today,))
    todays_guests = cursor.fetchall()

    # Fetch upcoming reservations
    cursor.execute('''
        SELECT name, reservation_date, reservation_time, number_of_guests
        FROM reservations
        WHERE DATE(reservation_date) > %s
        ORDER BY reservation_date ASC, reservation_time ASC
    ''', (today,))
    upcoming_guests = cursor.fetchall()

    cursor.close()
    db.close()

    admin_controls = {
        'Manage Menu Items': '/admin/menu',
        'Manage Signature Dishes': '/admin/signature',
        'Manage Vibe': '/admin/fusion-vibe',
        'Manage Gallery': '/admin/gallery',
        'Logout': '/admin/logout'
    }

    return render_template(
        'dashboard.html',
        admin_user=session['admin_user'],
        booking_count=booking_count,
        todays_guests=todays_guests,
        upcoming_guests=upcoming_guests,
        admin_controls=admin_controls
    )

# Logout
@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_user', None)
    return redirect('/admin/login')

# Homepage
@app.route('/')
def index():
    ensure_admin_table()
    conn = restaurant_db()
    cursor = conn.cursor(dictionary=True)

    cursor.execute('SELECT * FROM menu_items')
    menu_items = cursor.fetchall()

    cursor.execute('SELECT * FROM fusion_vibe')
    vibe_items = cursor.fetchall()

    cursor.execute('SELECT * FROM gallery')
    gallery_items = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('index.html', menu_items=menu_items, vibe_items=vibe_items, gallery_items=gallery_items)

# API: Signature Dishes
@app.route('/api/signature-dishes')
def get_signature_dishes():
    connection = restaurant_db()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM signature_dishes")
    dishes = cursor.fetchall()
    cursor.close()
    connection.close()
    return jsonify(dishes)

# API: Menu Items
@app.route('/api/menu')
def get_menu():
    connection = restaurant_db()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM menu_items")
    menu = cursor.fetchall()
    cursor.close()
    connection.close()
    return jsonify(menu)

# Reservations
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
        cursor.execute('''
            INSERT INTO reservations (name, email, phone, reservation_date, reservation_time, number_of_guests)
            VALUES (%s, %s, %s, %s, %s, %s)
        ''', (name, email, phone, reservation_date, reservation_time, number_of_guests))
        conn.commit()
        cursor.close()
        conn.close()
        flash('🎉 Reservation confirmed! See you soon at Fusion Affair!')
        return redirect('/')

    return render_template('reservations.html')


# New section: Admin Menu Management
from flask import Flask, render_template, request, redirect, session, url_for, flash
import os
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/admin/menu', methods=['GET', 'POST'])
def admin_menu():
    if 'admin_user' not in session:
        return redirect('/admin/login')

    db = restaurant_db()
    cursor = db.cursor(dictionary=True)

    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        price = request.form.get('price')
        image_file = request.files.get('image')

        if not name or not description or not price:
            flash('All fields are required, including price.')
        else:
            try:
                price = float(price)
                if image_file and allowed_file(image_file.filename):
                    filename = secure_filename(image_file.filename)
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    image_file.save(filepath)
                    image_url = f"/{filepath}"

                    cursor.execute("""
                        INSERT INTO menu_items (name, description, price, image_url)
                        VALUES (%s, %s, %s, %s)
                    """, (name, description, price, image_url))
                    db.commit()
                    flash('Menu item added successfully!')
                else:
                    flash('Image file missing or invalid format.')
            except ValueError:
                flash('Price must be a valid number.')


    cursor.execute("SELECT * FROM menu_items")
    menu_items = cursor.fetchall()
    cursor.close()
    db.close()

    return render_template('admin_menu.html', menu_items=menu_items)

@app.route('/admin/menu/delete/<int:item_id>')
def delete_menu_item(item_id):
    if 'admin_user' not in session:
        return redirect('/admin/login')

    db = restaurant_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM menu_items WHERE id = %s", (item_id,))
    db.commit()
    cursor.close()
    db.close()
    flash('Menu item deleted.')
    return redirect('/admin/menu')


from flask import Flask, render_template, request, redirect, session, url_for, jsonify, flash
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
import os
from werkzeug.utils import secure_filename


UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def restaurant_db():
    return mysql.connector.connect(
        host='127.0.0.1',
        port=3307,
        user="root",
        password="Mass8187879186",
        database="restaurant_db"
    )

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
@app.route('/admin/signature', methods=['GET', 'POST'])
@app.route('/admin/signature', methods=['GET', 'POST'])
def admin_signature():
    if 'admin_user' not in session:
        return redirect('/admin/login')

    db = restaurant_db()
    cursor = db.cursor(dictionary=True)

    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        price = request.form['price']
        image_file = request.files['image']

        if image_file and allowed_file(image_file.filename):
            filename = secure_filename(image_file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image_file.save(filepath)
            image_url = f"/static/uploads/{filename}"

            cursor.execute("""
                INSERT INTO signature_dishes (name, description, price, image_url)
                VALUES (%s, %s, %s, %s)
            """, (name, description, price, image_url))
            db.commit()
            flash('Signature dish added successfully!')

    cursor.execute("SELECT * FROM signature_dishes")
    signature_dishes = cursor.fetchall()
    cursor.close()
    db.close()

    return render_template('admin_signature.html', signature_dishes=signature_dishes)
@app.route('/admin/signature/edit/<int:dish_id>', methods=['GET', 'POST'])
def edit_signature_dish(dish_id):
    if 'admin_user' not in session:
        return redirect('/admin/login')

    db = restaurant_db()
    cursor = db.cursor(dictionary=True)

    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        price = request.form['price']
        image_file = request.files.get('image')

        if not name or not description or not price:
            flash('All fields are required.')
        else:
            try:
                price = float(price)
                if image_file and allowed_file(image_file.filename):
                    filename = secure_filename(image_file.filename)
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    image_file.save(filepath)
                    image_url = f"/static/uploads/{filename}"

                    cursor.execute("""
                        UPDATE signature_dishes
                        SET name=%s, description=%s, price=%s, image_url=%s
                        WHERE id=%s
                    """, (name, description, price, image_url, dish_id))
                else:
                    cursor.execute("""
                        UPDATE signature_dishes
                        SET name=%s, description=%s, price=%s
                        WHERE id=%s
                    """, (name, description, price, dish_id))

                db.commit()
                flash('Signature dish updated.')
                return redirect('/admin/signature')
            except ValueError:
                flash('Price must be a valid number.')

    cursor.execute("SELECT * FROM signature_dishes WHERE id = %s", (dish_id,))
    dish = cursor.fetchone()
    cursor.close()
    db.close()

    return render_template('edit_signature_dish.html', dish=dish)


@app.route('/admin/signature/delete/<int:dish_id>')
def delete_signature_dish(dish_id):
    if 'admin_user' not in session:
        return redirect('/admin/login')

    db = restaurant_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM signature_dishes WHERE id = %s", (dish_id,))
    db.commit()
    cursor.close()
    db.close()
    flash('Signature dish deleted.')
    return redirect('/admin/signature')
@app.route('/admin/menu/edit/<int:item_id>', methods=['GET', 'POST'])
def edit_menu_item(item_id):
    if 'admin_user' not in session:
        return redirect('/admin/login')

    db = restaurant_db()
    cursor = db.cursor(dictionary=True)

    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        price = request.form.get('price')
        image_file = request.files.get('image')

        if not name or not description or not price:
            flash('All fields are required.')
        else:
            try:
                price = float(price)
                if image_file and allowed_file(image_file.filename):
                    filename = secure_filename(image_file.filename)
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    image_file.save(filepath)
                    image_url = f"/static/uploads/{filename}"
                    cursor.execute('''
                        UPDATE menu_items
                        SET name=%s, description=%s, price=%s, image_url=%s
                        WHERE id=%s
                    ''', (name, description, price, image_url, item_id))
                else:
                    cursor.execute('''
                        UPDATE menu_items
                        SET name=%s, description=%s, price=%s
                        WHERE id=%s
                    ''', (name, description, price, item_id))

                db.commit()
                flash('Menu item updated successfully!')
                return redirect('/admin/menu')

            except ValueError:
                flash('Price must be a number.')

    cursor.execute("SELECT * FROM menu_items WHERE id = %s", (item_id,))
    item = cursor.fetchone()
    cursor.close()
    db.close()

    return render_template('edit_menu_item.html', item=item)


# --- Admin: Fusion Vibe Management ---

@app.route('/admin/fusion-vibe', methods=['GET', 'POST'])
def admin_fusion_vibe():
    if 'admin_user' not in session:
        return redirect('/admin/login')

    db = restaurant_db()
    cursor = db.cursor(dictionary=True)

    if request.method == 'POST':
        caption = request.form.get('caption')
        image_file = request.files.get('image')

        if image_file and allowed_file(image_file.filename):
            filename = secure_filename(image_file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image_file.save(filepath)
            image_url = f"/static/uploads/{filename}"

            cursor.execute("INSERT INTO fusion_vibe (image_url, caption) VALUES (%s, %s)",
                           (image_url, caption))
            db.commit()
            flash('Fusion vibe image added!')
        else:
            flash('Invalid image file.')

    cursor.execute("SELECT * FROM fusion_vibe")
    fusion_items = cursor.fetchall()
    cursor.close()
    db.close()

    return render_template('admin_fusion_vibe.html', fusion_items=fusion_items)


@app.route('/admin/fusion-vibe/delete/<int:item_id>')
def delete_fusion_vibe(item_id):
    if 'admin_user' not in session:
        return redirect('/admin/login')

    db = restaurant_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM fusion_vibe WHERE id = %s", (item_id,))
    db.commit()
    cursor.close()
    db.close()
    flash('Fusion vibe image deleted.')
    return redirect('/admin/fusion-vibe')



# --- Admin: Gallery Management ---

@app.route('/admin/gallery', methods=['GET', 'POST'])
def admin_gallery():
    if 'admin_user' not in session:
        return redirect('/admin/login')

    db = restaurant_db()
    cursor = db.cursor(dictionary=True)

    if request.method == 'POST':
        alt_text = request.form.get('alt_text')
        image_file = request.files.get('image')

        if image_file and allowed_file(image_file.filename):
            filename = secure_filename(image_file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image_file.save(filepath)
            image_url = f"/static/uploads/{filename}"

            cursor.execute("INSERT INTO gallery (image_url, alt_text) VALUES (%s, %s)",
                           (image_url, alt_text))
            db.commit()
            flash('Gallery image added!')
        else:
            flash('Invalid image file.')

    cursor.execute("SELECT * FROM gallery")
    gallery_items = cursor.fetchall()
    cursor.close()
    db.close()

    return render_template('admin_gallery.html', gallery_items=gallery_items)


@app.route('/admin/gallery/delete/<int:item_id>')
def delete_gallery(item_id):
    if 'admin_user' not in session:
        return redirect('/admin/login')

    db = restaurant_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM gallery WHERE id = %s", (item_id,))
    db.commit()
    cursor.close()
    db.close()
    flash('Gallery image deleted.')
    return redirect('/admin/gallery')


if __name__ == '__main__':
    app.run(debug=True)
