import sqlite3

def restaurant_db():
    conn = sqlite3.connect('restaurant.db')
    return conn

def create_all_tables():
    conn = restaurant_db()
    cursor = conn.cursor()

    # Admin Users Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admin_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    ''')

    # Menu Items Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS menu_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            price REAL NOT NULL,
            image_url TEXT NOT NULL
        )
    ''')

    # Signature Dishes Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS signature_dishes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            price REAL NOT NULL,
            image_url TEXT NOT NULL
        )
    ''')

    # Fusion Vibe Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS fusion_vibe (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            image_url TEXT NOT NULL,
            caption TEXT
        )
    ''')

    # Gallery Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS gallery (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            image_url TEXT NOT NULL,
            alt_text TEXT
        )
    ''')

    # Reservations Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reservations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT,
            phone TEXT,
            reservation_date TEXT,
            reservation_time TEXT,
            number_of_guests INTEGER,
            special_request TEXT
        )
    ''')

    conn.commit()
    cursor.close()
    conn.close()
    print("✅ Tables created successfully!")

if __name__ == '__main__':
    create_all_tables()
