from flask import Flask, request, jsonify

app = Flask(__name__)

# Ruta para recibir coordenadas
@app.route('/alert', methods=['POST'])
def recibir_alerta():
    data = request.json
    print(f"Alerta recibida: {data}")
    return jsonify({"status": "ok"}), 200

if __name__ == '__main__':
    app.run(debug=True)
