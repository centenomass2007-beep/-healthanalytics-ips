/* auth.js — Gestión de tokens JWT y protección de rutas */

const API = '/api';

function getToken() { return localStorage.getItem('access'); }
function getRefresh() { return localStorage.getItem('refresh'); }

async function authFetch(url, options = {}) {
  options.headers = options.headers || {};
  options.headers['Authorization'] = `Bearer ${getToken()}`;

  // No forzar Content-Type cuando el body es FormData (el browser agrega boundary)
  if (!(options.body instanceof FormData)) {
    options.headers['Content-Type'] = options.headers['Content-Type'] || 'application/json';
  }

  let res = await fetch(url, options);


  if (res.status === 401) {
    // Intenta refrescar token
    const refreshRes = await fetch(`${API}/auth/refresh/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh: getRefresh() })
    });
    if (refreshRes.ok) {
      const data = await refreshRes.json();
      localStorage.setItem('access', data.access);
      options.headers['Authorization'] = `Bearer ${data.access}`;
      res = await fetch(url, options);
    } else {
      cerrarSesion();
      return null;
    }
  }
  return res;
}

function cerrarSesion() {
  localStorage.clear();
  window.location.href = '/login/';
}

// Proteger páginas (redirige si no hay token)
(function protegerRuta() {
  const rutasPublicas = ['/login/'];
  if (!rutasPublicas.includes(window.location.pathname) && !getToken()) {
    window.location.href = '/login/';
  }
  // Mostrar nombre de usuario en sidebar
  const el = document.getElementById('usuario-nombre');
  if (el) {
    const username = localStorage.getItem('username') || '—';
    const rol = localStorage.getItem('rol') || '';
    el.textContent = `${username} · ${rol}`;
  }
})();

// Marca nav link activo con color blanco
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.sidebar .nav-link.active').forEach(el => {
    el.classList.remove('text-white-50');
    el.classList.add('text-white', 'bg-white', 'bg-opacity-10', 'rounded');
  });
});

async function descargarArchivo(url, filename) {
  try {
    const res = await authFetch(url);
    if (!res || !res.ok) {
      alert("Error al descargar el archivo");
      return;
    }
    const blob = await res.blob();
    const blobUrl = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = blobUrl;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(blobUrl);
  } catch (e) {
    console.error("Error descargando archivo:", e);
  }
}
