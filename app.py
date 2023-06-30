from flask import Flask, render_template, request, session, redirect, url_for, g
import sqlite3
import pandas as pd
import os

app = Flask(__name__)

def generate_secret_key():
    return os.urandom(16).hex()

# Set secret key
app.secret_key = generate_secret_key()

def generetader_motor_db():
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
                ''')
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


def generated_user_db():
    # Membuat koneksi ke database
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    # Membuat tabel motor
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        email TEXT NOT NULL,
                        username TEXT NOT NULL,
                        password TEXT NOT NULL
                    )''')

    # Commit perubahan dan menutup koneksi
    conn.commit()
    conn.close()

# Mengecek file users.db
if not os.path.exists('users.db'):
    print('membuat table user')
     # Jika belum ada maka akan membuat table databse baru
    generated_user_db()

# Mengecek file users.db
if not os.path.exists('motors.db'):
    print('membuat table motor')
    # Jika belum ada maka akan membuat table databse baru
    generetader_motor_db()

def get_user_db():
    if 'user_db' not in g:
        g.user_db = sqlite3.connect('users.db')
    return g.user_db

# Fungsi untuk menghubungkan ke database pemesanan
def get_order_db(user_id):
    if 'order_db' not in g:
        g.order_db = sqlite3.connect(f'order_{user_id}.db')
    return g.order_db

# Fungsi untuk membuat tabel pemesanan baru
def create_order_table(user_id):
    conn = get_order_db(user_id)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS orders (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        motor TEXT NOT NULL,
                        alamat TEXT NOT NULL,
                        haripemakaian INTEGER NOT NULL,
                        total INTEGER NOT NULL
                    )''')
    conn.commit()

def get_motor_connection():
    conn = sqlite3.connect('motors.db')
    conn.row_factory = sqlite3.Row
    return conn


def get_user_connection():
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row
    return conn


def get_all_motor():
    conn = get_motor_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM motor')
    motor = cursor.fetchall()
    conn.close()
    return motor

def get_current_user():
    user_id = session.get('user_id')
    username = session.get('username')
    if user_id and username:
        return {'id': user_id, 'username': username}
    return None

def is_logged_in():
    return 'user_name' in session and session['user_name'] != ''

def get_orders_data():
    conn = get_order_db(session['user_id'])
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM orders')
    orders_data = cursor.fetchall()
    conn.close()
    return orders_data

def analyze_orders():
    orders_data = get_orders_data()

    if len(orders_data) == 0:
        return None, None, None

    # Membuat DataFrame Pandas dari data pemesanan
    df = pd.DataFrame(orders_data, columns=['id', 'motor', 'alamat', 'haripemakaian', 'total'])

    # Pemesanan Terakhir
    order_terakhir = df['motor'].iloc[-1]
    avg_pemakaian = df['haripemakaian'].mean()
    ovr_total =  df['total'].sum()

    return order_terakhir, avg_pemakaian, ovr_total

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/logout', methods=['POST'])
def logout():
    # Hapus informasi pengguna dari sesi Flask
    session.pop('user_id', None)
    session.pop('user_name', None)
    session.pop('user_email', None)
    return redirect(url_for('index'))

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/login', methods=["POST"])
def login_validation():
    conn = get_user_connection()
    cursor = conn.cursor()
    username = request.form.get('username')
    password = request.form.get('password')
    cursor.execute('SELECT id, username, email FROM users WHERE username = ? AND password = ?', (username, password))
    user = cursor.fetchone()
    if user is not None:
        # Login berhasil, simpan informasi pengguna ke sesi Flask
        session['user_id'] = user['id']
        session['user_name'] = user['username']
        session['user_email'] = user['email']
        user_id = user['id']
        create_order_table(user_id)

        return redirect(url_for('profile'))
    else:
        return render_template('login.html', message="Username atau password salah.")
    
@app.route('/daftar')
def daftar():
    return render_template('daftar.html')
    
@app.route('/profile')
def profile():
    order_terakhir, avg_pemakaian, ovr_total = analyze_orders()
    return render_template('profile.html', 
                           order_terakhir=order_terakhir,
                           avg_pemakaian=avg_pemakaian,
                           ovr_total=ovr_total)

@app.route('/account', methods=['POST'])
def account():
    conn = get_user_connection()
    cursor = conn.cursor()

    email = request.form.get('email')
    username = request.form.get('username')
    password = request.form.get('password')

    cursor.execute('SELECT id FROM users WHERE email = ?', (email,))
    existing_user = cursor.fetchone()
    cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
    existing_user_username = cursor.fetchone()

    if existing_user is not None:
        return render_template('daftar.html', message="Email sudah terdaftar. Silakan gunakan email lain.")
    elif existing_user_username is not None:
        return render_template('daftar.html', message="Username sudah digunakan. Silakan pilih username lain.")
    else:
        # Tambahkan pengguna baru ke database
        cursor.execute('INSERT INTO users (email, username, password) VALUES (?, ?, ?)', (email, username, password))
        conn.commit()

        # Dapatkan ID pengguna baru dan buat tabel pemesanan
        cursor.execute('SELECT id FROM users WHERE email = ?', (email,))
        user_id = cursor.fetchone()['id']
        create_order_table(user_id)

        conn.close()
        return render_template('login.html', message="Akun Berhasil Dibuat. Silakan Login.")


@app.route('/motors', defaults={'tipe':None})
@app.route('/motors/<tipe>')
def motors(tipe):
    all_motor = get_all_motor()
    if tipe:
        filtered_motor = [m for m in all_motor if m['tipe'] == tipe]
        return render_template('koleksi.html', motor=filtered_motor)
    elif tipe:
        filtered_motor = [m for m in all_motor if m['nama'] == tipe]
        return render_template('koleksi.html', motor=filtered_motor)
    else:
        return render_template('koleksi.html', motor=all_motor)
    
@app.route('/details', methods=['POST'])
def details():
    motor_nama = request.form.get('motor_nama')
    motor_desc = request.form.get('motor_desc')
    motor_harga = request.form.get('motor_harga')
    motor_status = request.form.get('motor_status')
    motor_gambar = request.form.get('motor_gambar')

    return render_template('detail.html',motor_nama=motor_nama, motor_harga=motor_harga, motor_desc=motor_desc, motor_status=motor_status, motor_gambar=motor_gambar )

@app.route('/checkout', methods=["POST"])
def checkout():
    if not is_logged_in():
          return render_template('index.html', message="Login Terlebih Dahulu sebelum memulai pemesanan")
    motor_nama = request.form.get('motor_nama')
    motor_desc = request.form.get('motor_desc')
    motor_harga = request.form.get('motor_harga')
    motor_status = request.form.get('motor_status')
    motor_gambar = request.form.get('motor_gambar')
    return render_template('checkout.html', motor_nama=motor_nama, motor_harga=motor_harga, motor_desc=motor_desc, motor_status=motor_status, motor_gambar=motor_gambar )

@app.route('/payment', methods=['POST'])
def payment():
    motor_nama = request.form.get('motor_nama')
    motor_desc = request.form.get('motor_desc')
    motor_harga = int(request.form.get('motor_harga'))
    motor_status = request.form.get('motor_status')
    motor_gambar = request.form.get('motor_gambar')

    user_nama = request.form.get('nama')
    user_alamat = request.form.get('alamat')
    user_hari = int(request.form.get('hari'))
    user_kota = request.form.get('kota')
    user_antar = 10000 if request.form.get('antar') == 'on' else 0
    user_pembayaran = request.form.get('pembayaran')

    total = motor_harga * user_hari + user_antar

    user_id = session.get('user_id')

    # Menghubungkan ke database pemesanan pengguna
    conn_order = get_order_db(user_id)

    # Membuat tabel pemesanan baru jika belum ada
    create_order_table(user_id)
    cursor_order = conn_order.cursor()
    cursor_order.execute('''INSERT INTO orders (motor, alamat, haripemakaian, total)
                           VALUES (?, ?, ?, ?)''', (motor_nama, user_alamat, user_hari, total))
    conn_order.commit()

    return render_template('payment.html', user_antar=user_antar,user_nama=user_nama, user_alamat=user_alamat, user_hari=user_hari,user_kota=user_kota,user_pembayaran=user_pembayaran, total=total )

@app.route('/sukses', methods=['POST'])
def sukses():
    nominal = int(request.form.get('nomnial')) 
    total = int(request.form.get('total'))
    kembalian = nominal - total
    
    return render_template('sukses.html', kembalian=kembalian)


@app.route('/about')
def about():
    return render_template('about.html')



if __name__ == '__main__':
    app.run(debug=True)