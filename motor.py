import sqlite3

# Membuat koneksi ke database
conn = sqlite3.connect('motors.db')
cursor = conn.cursor()


# Membuat tabel motor
cursor.execute('''CREATE TABLE IF NOT EXISTS motor (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nama TEXT NOT NULL,
                    harga INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    tipe TEXT NOT NULL,
                    desc TEXT NOT NULL,
                    gambar TEXT NOT NULL
                )''')

# Menambahkan data motor
motor_data = [
    ('Nmax', 150000, 'Tersedia', 'matic','Yamaha Nmax-155cc', 'nmax.png'),
    ('Aerox', 180000, 'Tersedia', 'matic','Yamaha Aerox-155cc','aerox.png'),
    ('Duke', 200000, 'Tersedia', 'kopling','KTM Duke-250cc','duke.png'),
    ('CBR', 200000, 'Tersedia', 'kopling','Honda CBR-150cc','cbr.png'),
    ('Wave', 50000, 'Tersedia', 'bebek','Honda Wave-120cc','wave.png'),
    ('Revo', 60000, 'Tersedia', 'bebek','Honda Revo-110cc','revo.png'),
]

cursor.executemany('INSERT INTO motor (nama, harga, status, tipe, desc, gambar) VALUES (?, ?, ?, ?, ?, ?)', motor_data)

# Commit perubahan dan menutup koneksi
conn.commit()
conn.close()