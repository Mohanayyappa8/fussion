import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.getenv("DB_URL")

def create_all_tables():
    try:
        conn = psycopg2.connect(DB_URL)
        cursor = conn.cursor()

        # Admin Users Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS admin_users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(100) UNIQUE NOT NULL,
                password_hash TEXT NOT NULL
            )
        ''')

        # Reservations Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reservations (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT,
                phone TEXT,
                reservation_date DATE,
                reservation_time TIME,
                number_of_guests INTEGER,
                special_request TEXT
            )
        ''')

        # Menu Items Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS menu_items (
                id SERIAL PRIMARY KEY,
                name TEXT,
                description TEXT,
                price REAL,
                image_url TEXT
            )
        ''')

        # Signature Dishes Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS signature_dishes (
                id SERIAL PRIMARY KEY,
                name TEXT,
                description TEXT,
                price REAL,
                image_url TEXT
            )
        ''')

        # Fusion Vibe Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS fusion_vibe (
                id SERIAL PRIMARY KEY,
                image_url TEXT,
                caption TEXT
            )
        ''')

        # Gallery Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS gallery (
                id SERIAL PRIMARY KEY,
                image_url TEXT,
                alt_text TEXT
            )
        ''')

        conn.commit()
        cursor.close()
        conn.close()
        print("✅ Tables created successfully in PostgreSQL!")

    except Exception as e:
        print(f"❌ Error while creating tables: {e}")
