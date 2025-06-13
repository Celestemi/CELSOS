from flask import Blueprint, request, jsonify, current_app
from datetime import datetime
import sqlite3
from werkzeug.security import check_password_hash
import os
import re  
from functools import wraps
import phonenumbers

emergency_bp = Blueprint('emergency', __name__)

# Configuración de Twilio
TWILIO_ENABLED = False
twilio_client = None

try:
    from twilio.rest import Client
    TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
    TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
    TWILIO_PHONE = os.getenv('TWILIO_PHONE_NUMBER')
    
    if all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE]):
        twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        TWILIO_ENABLED = True
except ImportError:
    current_app.logger.warning("Twilio no está instalado. Las notificaciones SMS estarán desactivadas.")
except Exception as e:
    current_app.logger.error(f"Error al configurar Twilio: {str(e)}")

def get_db_connection():
    conn = sqlite3.connect(current_app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn

def validate_phone_number(phone):
    """Validación básica de número de teléfono usando expresiones regulares"""
    # Patrón simple: + seguido de 10-15 dígitos
    pattern = r'^\+\d{10,15}$'
    return re.match(pattern, phone) is not None

def validate_phone_number(phone):
    try:
        parsed = phonenumbers.parse(phone, None)
        return phonenumbers.is_valid_number(parsed)
    except:
        return False

def auth_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        data = request.get_json()
        if not data or 'user_id' not in data or 'auth_token' not in data:
            return jsonify({'error': 'Authentication required'}), 401
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE id = ?', (data['user_id'],)).fetchone()
        conn.close()
        
        if not user or not check_password_hash(user['password'], data['auth_token']):
            return jsonify({'error': 'Unauthorized'}), 401
        
        return f(*args, **kwargs)
    return decorated_function

@emergency_bp.route('/send_alert', methods=['POST'])
@auth_required
def send_emergency_alert():
    data = request.get_json()
    required_fields = ['user_id', 'message', 'location']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    try:
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO alerts (user_id, message, location, alert_type, status)
            VALUES (?, ?, ?, ?, ?)
        ''', (data['user_id'], data['message'], data['location'], 'emergency', 'active'))
        
        # Notificar contactos de emergencia
        if TWILIO_ENABLED:
            contacts = conn.execute('''
                SELECT phone FROM emergency_contacts 
                WHERE user_id = ? AND is_primary = 1
            ''', (data['user_id'],)).fetchall()
            
            for contact in contacts:
                try:
                    twilio_client.messages.create(
                        body=f"EMERGENCIA: {data['message']}. Ubicación: {data['location']}",
                        from_=TWILIO_PHONE,
                        to=contact['phone']
                    )
                except Exception as e:
                    current_app.logger.error(f"Error enviando SMS a {contact['phone']}: {str(e)}")
        
        conn.commit()
        return jsonify({
            'status': 'success',
            'message': 'Alerta de emergencia enviada',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        current_app.logger.error(f"Error en send_emergency_alert: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500
    finally:
        conn.close()

@emergency_bp.route('/contacts', methods=['GET', 'POST', 'DELETE'])
@auth_required
def manage_contacts():
    data = request.get_json() if request.method != 'GET' else {}
    user_id = request.args.get('user_id') or data.get('user_id')
    
    if not user_id:
        return jsonify({'error': 'user_id required'}), 400
    
    conn = get_db_connection()
    try:
        if request.method == 'GET':
            contacts = conn.execute('''
                SELECT * FROM emergency_contacts 
                WHERE user_id = ?
            ''', (user_id,)).fetchall()
            return jsonify({'contacts': [dict(contact) for contact in contacts]})
        
        elif request.method == 'POST':
            required_fields = ['name', 'phone']
            if not all(field in data for field in required_fields):
                return jsonify({'error': 'Missing required fields'}), 400
            
            if not validate_phone_number(data['phone']):
                return jsonify({'error': 'Invalid phone number'}), 400
            
            # Verificar si ya existe el contacto
            existing = conn.execute('''
                SELECT 1 FROM emergency_contacts 
                WHERE user_id = ? AND phone = ?
            ''', (user_id, data['phone'])).fetchone()
            
            if existing:
                return jsonify({'error': 'Contact already exists'}), 400
            
            conn.execute('''
                INSERT INTO emergency_contacts 
                (user_id, name, phone, email, relationship, is_primary)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                user_id,
                data['name'],
                data['phone'],
                data.get('email'),
                data.get('relationship'),
                data.get('is_primary', False)
            ))
            conn.commit()
            return jsonify({'status': 'success'})
        
        elif request.method == 'DELETE':
            contact_id = request.args.get('contact_id')
            if not contact_id:
                return jsonify({'error': 'contact_id required'}), 400
            
            conn.execute('DELETE FROM emergency_contacts WHERE id = ? AND user_id = ?', 
                        (contact_id, user_id))
            conn.commit()
            return jsonify({'status': 'success'})
            
    except Exception as e:
        current_app.logger.error(f"Error in manage_contacts: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500
    finally:
        conn.close()