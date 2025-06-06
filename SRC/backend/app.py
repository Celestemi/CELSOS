from flask import Flask, request, jsonify, send_from_directory
import os

app = Flask(__name__, static_folder='../frontend', static_url_path='')

alerts = []

@app.route('/')
def serve_frontend():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory(app.static_folder, path)

@app.route('/alert', methods=['POST'])
def alert():
    data = request.json
    alerts.append(data)
    return jsonify({"message": "Alerta recibida"}), 200

@app.route('/alerts', methods=['GET'])
def get_alerts():
    return jsonify(alerts), 200

if __name__ == '__main__':
    app.run(debug=True)