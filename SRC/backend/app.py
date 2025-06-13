from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, g
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime
import os
import sqlite3
import sys

app = Flask(__name__)
app.secret_key = 'tu_clave_secreta_aqui' 

# Configuración de la base de datos
app.config['DATABASE'] = os.path.join(os.path.dirname(__file__), 'database.db')

try:
    from core.emergency import emergency_bp
    app.register_blueprint(emergency_bp, url_prefix='/emergency')
except ImportError as e:
    print(f"ERROR: No se pudo importar el blueprint de emergencia: {e}", file=sys.stderr)

# Funciones de base de datos
def get_db():
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn

# Decorador para rutas protegidas
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Por favor inicia sesión para acceder a esta página', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# Validación de contraseña
def validate_password(password):
    if len(password) < 8:
        return "La contraseña debe tener al menos 8 caracteres"
    if not any(c.isupper() for c in password):
        return "La contraseña debe contener al menos una mayúscula"
    if not any(c.isdigit() for c in password):
        return "La contraseña debe contener al menos un número"
    if not any(c in '!@#$%^&*(),.?":{}|<>' for c in password):
        return "La contraseña debe contener al menos un carácter especial"
    return None

# Rutas principales
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    conn.close()
    
    if user and check_password_hash(user['password'], password):
        session['user_id'] = user['id']
        session['username'] = user['username']
        session['fullname'] = user['fullname']
        flash(f'Bienvenido {user["fullname"]}!', 'success')
        return redirect(url_for('dashboard'))
    else:
        flash('Usuario o contraseña incorrectos', 'error')
        return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    
    # Obtener datos del formulario
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()
    email = request.form.get('email', '').strip()
    fullname = request.form.get('fullname', '').strip()
    confirm_password = request.form.get('confirm_password', '').strip()
    
    # Validaciones básicas
    if not all([username, password, email, fullname, confirm_password]):
        flash('Todos los campos son obligatorios', 'error')
        return redirect(url_for('register'))
    
    if password != confirm_password:
        flash('Las contraseñas no coinciden', 'error')
        return redirect(url_for('register'))
    
    password_error = validate_password(password)
    if password_error:
        flash(password_error, 'error')
        return redirect(url_for('register'))
    
    hashed_password = generate_password_hash(password)
    
    conn = get_db()
    try:
        conn.execute('INSERT INTO users (username, password, email, fullname) VALUES (?, ?, ?, ?)',
                    (username, hashed_password, email, fullname))
        conn.commit()
        flash('Registro exitoso. Por favor inicia sesión.', 'success')
    except sqlite3.IntegrityError as e:
        if 'username' in str(e):
            flash('El nombre de usuario ya está en uso', 'error')
        elif 'email' in str(e):
            flash('El correo electrónico ya está registrado', 'error')
        else:
            flash('Error al registrar el usuario', 'error')
    except Exception as e:
        flash('Ocurrió un error inesperado', 'error')
        # Considera loggear el error (e) para debugging
    finally:
        conn.close()
    
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    # Obtener historial de alertas del usuario
    conn = get_db()
    alerts = conn.execute('''
        SELECT * FROM alerts 
        WHERE user_id = ? 
        ORDER BY created_at DESC
        LIMIT 10
    ''', (session['user_id'],)).fetchall()
    conn.close()
    
    return render_template('dashboard.html', 
                         user={
                             'username': session['username'],
                             'fullname': session['fullname']
                         },
                         alerts=alerts)

@app.route('/api/panic', methods=['POST'])
@login_required
def panic_alert():
    data = request.get_json()
    
    # Guardar en base de datos
    conn = get_db()
    conn.execute('''
        INSERT INTO alerts (user_id, latitude, longitude, address, alert_type)
        VALUES (?, ?, ?, ?, ?)
    ''', (session['user_id'], data['lat'], data['lng'], data['address'], 'emergency'))
    conn.commit()
    
    conn.close()
    return jsonify({'status': 'success', 'message': 'Alerta enviada'})

@app.route('/api/history')
@login_required
def get_history():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    offset = (page - 1) * per_page
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Obtener alertas paginadas
    cursor.execute('''
        SELECT *, datetime(created_at, 'localtime') as local_time 
        FROM alerts 
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT ? OFFSET ?
    ''', (session['user_id'], per_page, offset))
    alerts = cursor.fetchall()
    
    # Contar total de alertas
    cursor.execute('SELECT COUNT(*) FROM alerts WHERE user_id = ?', (session['user_id'],))
    total = cursor.fetchone()[0]
    
    conn.close()
    
    return jsonify({
        'alerts': [dict(alert) for alert in alerts],
        'total': total,
        'page': page,
        'per_page': per_page,
        'total_pages': (total + per_page - 1) // per_page
    })

@app.route('/api/update_theme', methods=['POST'])
@login_required
def update_theme():
    if not request.is_json:
        return jsonify({'error': 'Request must be JSON'}), 400
    
    theme = request.json.get('theme')
    if not theme:
        return jsonify({'error': 'Theme not provided'}), 400
    
    valid_themes = ['theme-light', 'theme-dark', 'theme-blue']
    if theme not in valid_themes:
        return jsonify({'error': 'Invalid theme'}), 400
    
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE users SET theme = ? WHERE id = ?',
            (theme, session['user_id'])
        )
        conn.commit()
        return jsonify({'status': 'success', 'theme': theme})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if conn:
            conn.close()

@app.route('/logout')
def logout():
    session.clear()
    flash('Has cerrado sesión correctamente', 'info')
    return redirect(url_for('index'))

@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'db_conn'):
        g.db_conn.close()

def init_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username VARCHAR(50) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                fullname VARCHAR(100) NOT NULL,
                theme VARCHAR(20) DEFAULT 'theme-dark',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                latitude DECIMAL(10, 8),
                longitude DECIMAL(11, 8),
                address TEXT,
                alert_type VARCHAR(50) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS emergency_contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name VARCHAR(100) NOT NULL,
                phone VARCHAR(20) NOT NULL,
                email VARCHAR(100),
                relationship VARCHAR(50),
                is_primary BOOLEAN DEFAULT FALSE,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        ''')
        db.commit()

if __name__ == '__main__':
    init_db()
    app.run(debug=True)