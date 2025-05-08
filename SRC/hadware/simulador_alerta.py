import requests

data = {
    "lat": -12.0464,
    "lng": -77.0428,
    "hora": "17:40",
    "fecha": "08/05/2025"
}

response = requests.post("http://localhost:5000/alert", json=data)
print("Respuesta:", response.json())
