let map, myMarker;

function login() {
  const u = document.getElementById('user').value;
  const p = document.getElementById('pass').value;

  if (u === "admin" && p === "celsos123") {
    document.getElementById('login').classList.add('hidden');
    document.getElementById('mainApp').classList.remove('hidden');
    initMap();
  } else {
    alert("❌ Usuario o contraseña incorrectos.");
  }
}

function initMap() {
  map = L.map('map').setView([-12.0464, -77.0428], 13);
  L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
    maxZoom: 18,
  }).addTo(map);
}

function getMyLocation() {
  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(position => {
      const lat = position.coords.latitude;
      const lng = position.coords.longitude;
      if (myMarker) map.removeLayer(myMarker);
      myMarker = L.marker([lat, lng]).addTo(map)
        .bindPopup("📍 Estás aquí").openPopup();
      map.setView([lat, lng], 16);
    });
  } else {
    alert("Tu navegador no soporta geolocalización.");
  }
}

function sendPanicAlert() {
  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(position => {
      const data = {
        lat: position.coords.latitude,
        lng: position.coords.longitude,
        hora: new Date().toLocaleTimeString(),
        fecha: new Date().toLocaleDateString()
      };
      fetch('/alert', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      })
      .then(res => res.json())
      .then(res => {
        const table = document.querySelector("#historyTable tbody");
        const row = `<tr><td>${data.fecha}</td><td>${data.hora}</td><td>${data.lat.toFixed(4)}, ${data.lng.toFixed(4)}</td></tr>`;
        table.innerHTML += row;

        const audio = new Audio("assets/sounds/alert.wav");
        audio.play();

        alert("🚨 Alerta enviada con éxito");
      })
      .catch(err => alert("Error al enviar alerta."));
    });
  } else {
    alert("Tu navegador no soporta geolocalización.");
  }
}

function shareLocation() {
  if (myMarker) {
    const latlng = myMarker.getLatLng();
    const url = `https://www.google.com/maps?q=${latlng.lat},${latlng.lng}`;
    navigator.clipboard.writeText(url).then(() => {
      alert(`🔗 Enlace copiado al portapapeles:\n${url}`);
    });
  } else {
    alert("Primero obtén tu ubicación.");
  }
}

function changeTheme() {
  const theme = document.getElementById("theme").value;
  document.body.className = theme;
}