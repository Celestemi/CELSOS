// Mapa y marcador global
let map;
let userMarker;
let userLocation = null;

// Inicializar mapa cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    initMap();
    setupEventListeners();
    loadHistory();
    setThemeFromCookie();
});

function initMap() {
    // Configuración inicial del mapa (centrado en Lima como fallback)
    map = L.map('map').setView([-12.0464, -77.0428], 13);
    
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);
    
    // Intenta obtener la ubicación del usuario al cargar
    getMyLocation();
}

function setupEventListeners() {
    // Botón de pánico
    document.getElementById('panicButton').addEventListener('click', sendPanicAlert);
    
    // Botón de obtener ubicación
    document.getElementById('getLocation').addEventListener('click', getMyLocation);
    
    // Botón de compartir ubicación
    document.getElementById('shareLocation').addEventListener('click', shareLocation);
    
    // Botón de búsqueda
    document.getElementById('searchButton').addEventListener('click', searchLocation);
    
    // Selector de tema
    document.getElementById('themeSelect').addEventListener('change', changeTheme);
    
    // Botón de logout
    document.getElementById('logout').addEventListener('click', logoutUser);
}

function getMyLocation() {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            position => {
                userLocation = {
                    lat: position.coords.latitude,
                    lng: position.coords.longitude
                };
                
                // Centrar mapa en la ubicación del usuario
                map.setView([userLocation.lat, userLocation.lng], 15);
                
                // Agregar o actualizar marcador
                if (userMarker) {
                    userMarker.setLatLng([userLocation.lat, userLocation.lng]);
                } else {
                    userMarker = L.marker([userLocation.lat, userLocation.lng], {
                        title: "Tu ubicación",
                        draggable: false
                    }).addTo(map).bindPopup("Estás aquí");
                }
                
                // Obtener dirección (opcional)
                getAddressFromCoords(userLocation.lat, userLocation.lng);
            },
            error => {
                console.error("Error obteniendo ubicación:", error);
                alert("No se pudo obtener tu ubicación. Asegúrate de habilitar los permisos de geolocalización.");
            }
        );
    } else {
        alert("Tu navegador no soporta geolocalización");
    }
}

function sendPanicAlert() {
    if (!userLocation) {
        alert("Primero obtén tu ubicación actual");
        return;
    }
    
    // Obtener dirección aproximada
    getAddressFromCoords(userLocation.lat, userLocation.lng, function(address) {
        const alertData = {
            lat: userLocation.lat,
            lng: userLocation.lng,
            address: address || "Ubicación desconocida"
        };
        
        // Enviar al servidor
        fetch('/api/panic', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(alertData)
        })
        .then(response => response.json())
        .then(data => {
            alert("¡Alerta de emergencia enviada!\n" + 
                 `Ubicación: ${alertData.address}\n` +
                 `Coordenadas: ${alertData.lat}, ${alertData.lng}`);
            loadHistory(); // Actualizar historial
        })
        .catch(error => {
            console.error("Error:", error);
            alert("Error al enviar alerta");
        });
    });
}

function shareLocation() {
    if (!userLocation) {
        alert("Primero obtén tu ubicación actual");
        return;
    }
    
    const mapUrl = `https://www.openstreetmap.org/?mlat=${userLocation.lat}&mlon=${userLocation.lng}#map=16/${userLocation.lat}/${userLocation.lng}`;
    
    if (navigator.share) {
        navigator.share({
            title: 'Mi ubicación actual',
            text: 'Estoy aquí:',
            url: mapUrl
        }).catch(err => {
            console.log('Error al compartir:', err);
            copyToClipboard(mapUrl);
        });
    } else {
        copyToClipboard(mapUrl);
    }
}

function searchLocation() {
    const query = document.getElementById('searchInput').value.trim();
    if (!query) return;
    
    // Usar Nominatim (OpenStreetMap) para geocodificación
    fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query)}`)
        .then(response => response.json())
        .then(data => {
            if (data && data.length > 0) {
                const result = data[0];
                const lat = parseFloat(result.lat);
                const lon = parseFloat(result.lon);
                
                map.setView([lat, lon], 15);
                L.marker([lat, lon]).addTo(map)
                    .bindPopup(`<b>${result.display_name}</b>`)
                    .openPopup();
            } else {
                alert("Ubicación no encontrada");
            }
        })
        .catch(error => {
            console.error("Error buscando ubicación:", error);
            alert("Error al buscar ubicación");
        });
}

function loadHistory() {
    fetch('/api/history')
        .then(response => response.json())
        .then(data => {
            const tbody = document.querySelector('#historyTable tbody');
            tbody.innerHTML = '';
            
            data.forEach(alert => {
                const date = new Date(alert.local_time);
                const row = document.createElement('tr');
                
                row.innerHTML = `
                    <td>${date.toLocaleDateString()}</td>
                    <td>${date.toLocaleTimeString()}</td>
                    <td>${alert.address || 'Ubicación desconocida'}</td>
                `;
                
                tbody.appendChild(row);
            });
        })
        .catch(error => {
            console.error("Error cargando historial:", error);
        });
}

function changeTheme() {
    const themeSelect = document.getElementById('themeSelect');
    const selectedTheme = themeSelect.value;
    
    // Cambiar clase en el body
    document.body.className = selectedTheme;
    
    // Guardar en cookie (persistencia)
    document.cookie = `theme=${selectedTheme}; path=/; max-age=31536000`; // 1 año
}

function setThemeFromCookie() {
    const cookies = document.cookie.split(';');
    for (const cookie of cookies) {
        const [name, value] = cookie.trim().split('=');
        if (name === 'theme') {
            document.body.className = value;
            document.getElementById('themeSelect').value = value;
            break;
        }
    }
}

function logoutUser() {
    fetch('/logout', {
        method: 'POST',
    })
    .then(response => {
        if (response.ok) {
            window.location.href = '/';
        }
    })
    .catch(error => {
        console.error('Error al cerrar sesión:', error);
        alert('Error al intentar cerrar sesión');
    });
}

// Helper para obtener dirección a partir de coordenadas
function getAddressFromCoords(lat, lng, callback) {
    fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lng}`)
        .then(response => response.json())
        .then(data => {
            const address = data.display_name;
            if (callback) callback(address);
            
            // Actualizar la interfaz
            document.getElementById('coordinates').textContent = `${lat.toFixed(4)}, ${lng.toFixed(4)}`;
            document.getElementById('address').textContent = address || "Ubicación desconocida";
            
            return address;
        })
        .catch(error => {
            console.error("Error obteniendo dirección:", error);
            if (callback) callback(null);
            
            document.getElementById('coordinates').textContent = `${lat.toFixed(4)}, ${lng.toFixed(4)}`;
            document.getElementById('address').textContent = "Dirección no disponible";
            
            return null;
        });
}

// Helper para copiar al portapapeles
function copyToClipboard(text) {
    const textarea = document.createElement('textarea');
    textarea.value = text;
    document.body.appendChild(textarea);
    textarea.select();
    document.execCommand('copy');
    document.body.removeChild(textarea);
    alert("Enlace copiado al portapapeles:\n" + text);
}