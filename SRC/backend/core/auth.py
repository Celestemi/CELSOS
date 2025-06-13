from flask import Blueprint, render_template, request, redirect, session, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from functools import wraps
from datetime import datetime
import re

bp = Blueprint('auth', __name__)
db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False) 
    fullname = db.Column(db.String(120), nullable=False) 
    password_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Decorador para rutas que requieren autenticación
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Por favor inicia sesión para acceder a esta página', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    if len(password) < 8:
        return False, 'La contraseña debe tener al menos 8 caracteres'
    return True, ''

@bp.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        if not username or not password:
            flash('Usuario y contraseña son requeridos', 'error')
            return redirect(url_for('auth.login'))
        
        user = User.query.filter_by(username=username).first()
        
        if not user or not user.check_password(password):
            flash('Usuario o contraseña incorrectos', 'error')
            return redirect(url_for('auth.login'))
            
        if not user.is_active:
            flash('Tu cuenta está desactivada', 'error')
            return redirect(url_for('auth.login'))
            
        session['user_id'] = user.id
        session['username'] = user.username
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        flash('Inicio de sesión exitoso', 'success')
        return redirect(url_for('emergency.dashboard'))
    
    return render_template('index.html')

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        fullname = request.form.get('fullname', '').strip()
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        
        # Validaciones
        if not all([username, email, fullname, password, confirm_password]):
            flash('Todos los campos son requeridos', 'error')
            return redirect(url_for('auth.register'))
            
        if password != confirm_password:
            flash('Las contraseñas no coinciden', 'error')
            return redirect(url_for('auth.register'))
            
        is_valid, msg = validate_password(password)
        if not is_valid:
            flash(msg, 'error')
            return redirect(url_for('auth.register'))
            
        if not validate_email(email):
            flash('Por favor ingresa un email válido', 'error')
            return redirect(url_for('auth.register'))
            
        if User.query.filter_by(username=username).first():
            flash('El nombre de usuario ya existe', 'error')
            return redirect(url_for('auth.register'))
            
        if User.query.filter_by(email=email).first():  
            flash('El correo electrónico ya está registrado', 'error')
            return redirect(url_for('auth.register'))
            
        try:
            new_user = User(
                username=username,
                email=email,
                fullname=fullname,
                is_active=True
            )
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            
            flash('Registro exitoso. Por favor inicia sesión.', 'success')
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            db.session.rollback()
            flash('Ocurrió un error durante el registro. Por favor intenta nuevamente.', 'error')
            return redirect(url_for('auth.register'))
    
    return render_template('register.html')

@bp.route('/logout')
@login_required
def logout():
    session.clear()
    flash('Has cerrado sesión correctamente', 'info')
    return redirect(url_for('auth.login'))