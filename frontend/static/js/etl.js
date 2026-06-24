/* etl.js — Ejecución ETL, subida de archivo, historial */

async function ejecutarETL() {
  const btn = document.getElementById('btn-run-etl');
  const progress = document.getElementById('etl-progress');

  btn.disabled = true;
  progress.classList.remove('d-none');

  try {
    const res = await authFetch('/api/etl/run/', { method: 'POST' });
    if (!res) return;
    const data = await res.json();

    if (res.ok) {
      mostrarResultado(data);
      cargarHistorial();
    } else {
      alert('Error: ' + (data.error || 'No se pudo ejecutar el ETL'));
    }
  } catch(e) {
    alert('Error de conexión: ' + e.message);
  } finally {
    btn.disabled = false;
    progress.classList.add('d-none');
  }
}

async function subirDataset() {
  const input = document.getElementById('archivo-dataset');
  if (!input.files.length) { alert('Selecciona un archivo primero.'); return; }

  const formData = new FormData();
  formData.append('archivo', input.files[0]);

  const progress = document.getElementById('etl-progress');
  progress.classList.remove('d-none');

  try {
    const csrfToken = getCsrfToken();

    const res = await authFetch('/api/etl/upload/', {
      method: 'POST',
      headers: {
        // authFetch ya agrega Authorization. Aquí solo CSRF.
        'X-CSRFToken': csrfToken
      },
      body: formData
    });

    if (!res) return;

    // Intentar parsear JSON tanto si ok como si falla.
    const data = await res.json().catch(() => ({}));

    if (res.ok) {
      mostrarResultado(data);
      cargarHistorial();
    } else {
      const detalle = data.detalle || data.message || data.error || JSON.stringify(data);
      alert(`Error al subir: ${detalle}`);
    }
  } catch (e) {
    alert('Error de conexión: ' + e.message);
  } finally {
    progress.classList.add('d-none');
  }
}

// subirDataset() definido una sola vez arriba (evita sobrescritura).

function mostrarResultado(data) {
  const estadoBadge = data.estado === 'completado'
    ? '<span class="badge bg-success">✓ Completado</span>'
    : '<span class="badge bg-danger">✗ Error</span>';

  document.getElementById('etl-metricas').innerHTML = `
    <div class="border rounded p-2 text-center small flex-fill" style="min-width:120px">
      <div class="text-muted">Registros Entrada</div>
      <div class="fw-bold h5 text-primary mb-0">${data.registros_entrada ?? 0}</div>
    </div>
    <div class="border rounded p-2 text-center small flex-fill" style="min-width:120px">
      <div class="text-muted">Registros Limpios</div>
      <div class="fw-bold h5 text-success mb-0">${data.registros_limpios ?? 0}</div>
    </div>
    <div class="border rounded p-2 text-center small flex-fill" style="min-width:120px">
      <div class="text-muted">Duplicados</div>
      <div class="fw-bold h5 text-warning mb-0">${data.duplicados_eliminados ?? 0}</div>
    </div>
    <div class="border rounded p-2 text-center small flex-fill" style="min-width:120px">
      <div class="text-muted">Tiempo (seg)</div>
      <div class="fw-bold h5 text-info mb-0">${data.tiempo_ejecucion_seg ?? 0}s</div>
    </div>
    <div class="w-100 text-center mt-1">${estadoBadge}</div>
  `;

  const logEl = document.getElementById('etl-log');
  logEl.textContent = data.log_detalle || 'Sin log disponible';
  logEl.classList.add('d-none');

  const btn = document.getElementById('btn-toggle-log');
  if (data.log_detalle && data.log_detalle.length > 50) {
    btn.classList.remove('d-none');
    btn.innerHTML = '<i class="bi bi-eye me-1"></i>Ver';
  } else {
    btn.classList.add('d-none');
  }
}

function toggleLog() {
  const logEl = document.getElementById('etl-log');
  const btn = document.getElementById('btn-toggle-log');
  const hidden = logEl.classList.contains('d-none');
  logEl.classList.toggle('d-none');
  btn.innerHTML = hidden
    ? '<i class="bi bi-eye-slash me-1"></i>Ocultar'
    : '<i class="bi bi-eye me-1"></i>Ver';
}

async function cargarHistorial() {
  try {
    const res = await authFetch('/api/etl/historial/');
    if (!res) return;
    const data = await res.json();

    const tbody = document.getElementById('historial-tbody');
    if (!data.length) {
      tbody.innerHTML = '<tr><td colspan="7" class="text-center text-muted py-4">Sin registros ETL</td></tr>';
      return;
    }

    tbody.innerHTML = data.map(r => `
      <tr>
        <td class="small">${formatFecha(r.fecha_ejecucion)}</td>
        <td class="small">${r.usuario_nombre || '—'}</td>
        <td><span class="badge bg-secondary">${r.registros_entrada}</span></td>
        <td><span class="badge bg-success">${r.registros_limpios}</span></td>
        <td><span class="badge bg-warning text-dark">${r.duplicados_eliminados}</span></td>
        <td class="small">${r.tiempo_ejecucion_seg}s</td>
        <td><span class="badge ${badgeEstado(r.estado)}">${r.estado}</span></td>
      </tr>
    `).join('');
  } catch(e) {
    console.error('Error historial:', e);
  }
}

function formatFecha(f) {
  return f ? new Date(f).toLocaleString('es-CO', { dateStyle:'short', timeStyle:'short' }) : '—';
}
function badgeEstado(e) {
  return { completado:'bg-success', error:'bg-danger',
           en_proceso:'bg-warning text-dark', pendiente:'bg-secondary' }[e] || 'bg-secondary';
}

function getCsrfToken() {
  // Django: leer cookie csrftoken (estándar)
  const name = 'csrftoken';
  const cookies = document.cookie ? document.cookie.split(';') : [];
  for (const c of cookies) {
    const cookie = c.trim();
    if (cookie.startsWith(name + '=')) {
      return decodeURIComponent(cookie.substring(name.length + 1));
    }
  }
  return '';
}

document.addEventListener('DOMContentLoaded', cargarHistorial);

