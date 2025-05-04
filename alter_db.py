import sqlite3

def add_special_request_column():
    conn = sqlite3.connect('restaurant.db')
    cursor = conn.cursor()
    try:
        cursor.execute('ALTER TABLE reservations ADD COLUMN special_request TEXT')
        print("✅ Column 'special_request' added.")
    except sqlite3.OperationalError as e:
        print(f"⚠️ Skipped: {e}")
    conn.commit()
    cursor.close()
    conn.close()

if __name__ == '__main__':
    add_special_request_column()
