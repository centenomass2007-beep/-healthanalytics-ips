/* pacientes.js — Listado de pacientes con filtros y paginación */

let paginaActual = 1;
let totalPaginas = 1;
let todosLosPacientes = [];
let timeoutBusqueda = null;

async function cargarPacientes(pagina = 1) {
  paginaActual = pagina;
  const riesgo   = document.getElementById('filtro-riesgo').value;
  const sexo     = document.getElementById('filtro-sexo').value;
  const critico  = document.getElementById('filtro-critico').checked;
  const busqueda = document.getElementById('busqueda').value.trim();

  let url = `/api/pacientes/?page=${pagina}`;
  if (riesgo)   url += `&riesgo=${riesgo}`;
  if (sexo)     url += `&sexo=${sexo}`;
  if (critico)  url += `&critico=true`;
  if (busqueda) url += `&busqueda=${encodeURIComponent(busqueda)}`;

  const tbody = document.getElementById('pacientes-tbody');
  tbody.innerHTML = `<tr><td colspan="11" class="text-center py-4">
    <div class="spinner-border spinner-border-sm me-2"></div>Cargando...
  </td></tr>`;

  try {
    const res = await authFetch(url);
    if (!res) return;
    const data = await res.json();

    const resultados = data.results ?? data;
    const total = data.count ?? resultados.length;
    totalPaginas = data.next || data.previous ? Math.ceil(total / 50) : 1;

    todosLosPacientes = resultados;
    renderTabla(resultados);
    document.getElementById('badge-total').textContent = total;
    document.getElementById('pagination-info').textContent =
      `Mostrando ${resultados.length} de ${total} pacientes`;
    renderPaginacion();
  } catch(e) {
    tbody.innerHTML = `<tr><td colspan="11" class="text-center text-danger py-4">
      Error al cargar datos: ${e.message}
    </td></tr>`;
  }
}

function renderTabla(pacientes) {
  const tbody = document.getElementById('pacientes-tbody');
  if (!pacientes.length) {
    tbody.innerHTML = '<tr><td colspan="11" class="text-center text-muted py-5">Sin pacientes encontrados</td></tr>';
    return;
  }

  const BADGE_RIESGO = {
    bajo:    'bg-success',
    medio:   'bg-warning text-dark',
    alto:    'bg-orange text-white',
    critico: 'bg-danger',
  };

  var puedePredecir = ['administrador', 'analista'].indexOf(localStorage.getItem('rol') || getRol()) !== -1;
  tbody.innerHTML = pacientes.map(p => `
    <tr class="${p.es_critico ? 'table-danger' : ''}">
      <td class="fw-semibold text-primary">${p.id_paciente}</td>
      <td>${p.nombres} ${p.apellidos}</td>
      <td>${p.edad ?? '—'}</td>
      <td>${p.sexo === 'M' ? '♂' : p.sexo === 'F' ? '♀' : '—'}</td>
      <td>${p.imc ? p.imc.toFixed(1) : '—'}
          ${p.clasificacion_imc ? `<br><small class="text-muted">${p.clasificacion_imc.replace('_',' ')}</small>` : ''}</td>
      <td class="${p.glucosa > 126 ? 'text-danger fw-semibold' : ''}">${p.glucosa ?? '—'}</td>
      <td class="${p.presion_sistolica > 140 ? 'text-danger fw-semibold' : ''}">${p.presion_sistolica ?? '—'}</td>
      <td class="small">${p.diagnostico_preliminar || '—'}</td>
      <td><span class="badge ${BADGE_RIESGO[p.riesgo_enfermedad] || 'bg-secondary'}">
        ${p.riesgo_enfermedad || '—'}
      </span></td>
      <td>${p.es_critico
        ? '<i class="bi bi-exclamation-triangle-fill text-danger" title="Paciente crítico"></i>'
        : '<i class="bi bi-check-circle text-success"></i>'}</td>
      <td>${puedePredecir
        ?      '<button class="btn btn-sm btn-outline-primary" onclick="predecirRiesgo(' + p.id_paciente + ')" title="Predecir riesgo"><i class="bi bi-cpu"></i></button>'
        : ''}</td>
    </tr>
  `).join('');
}

function buscarGlobal() {
  if (timeoutBusqueda) clearTimeout(timeoutBusqueda);
  timeoutBusqueda = setTimeout(function() { cargarPacientes(1); }, 300);
}

function renderPaginacion() {
  const ctrl = document.getElementById('pagination-controls');
  if (totalPaginas <= 1) { ctrl.innerHTML = ''; return; }

  let html = `
    <button class="btn btn-sm btn-outline-secondary" onclick="cargarPacientes(${paginaActual-1})"
            ${paginaActual === 1 ? 'disabled' : ''}>
      <i class="bi bi-chevron-left"></i>
    </button>`;
  for (let i = Math.max(1, paginaActual-2); i <= Math.min(totalPaginas, paginaActual+2); i++) {
    html += `<button class="btn btn-sm ${i === paginaActual ? 'btn-primary' : 'btn-outline-secondary'}"
               onclick="cargarPacientes(${i})">${i}</button>`;
  }
  html += `
    <button class="btn btn-sm btn-outline-secondary" onclick="cargarPacientes(${paginaActual+1})"
            ${paginaActual === totalPaginas ? 'disabled' : ''}>
      <i class="bi bi-chevron-right"></i>
    </button>`;
  ctrl.innerHTML = html;
}

async function predecirRiesgo(pacienteId) {
  var body = document.getElementById('prediccion-body');
  body.innerHTML = '<div class="text-center py-4"><div class="spinner-border text-primary"></div><p class="mt-2">Procesando predicción...</p></div>';
  var modal = new bootstrap.Modal(document.getElementById('modal-prediccion'));
  modal.show();
  try {
    var res = await authFetch('/api/ml/predecir/', {
      method: 'POST',
      body: JSON.stringify({ paciente_id: pacienteId }),
    });
    if (!res) return;
    var data = await res.json();
    if (!res.ok) {
      body.innerHTML = '<div class="alert alert-danger mb-0">' + (data.error || 'Error al predecir') + '</div>';
      return;
    }
    var riesgo = data.riesgo_predicho || '—';
    var prob = data.probabilidad != null ? (data.probabilidad * 100).toFixed(1) + '%' : '—';
    var diag = data.diagnostico_detallado || '—';
    var reco = data.recomendaciones || '';
    var badgeColor = { bajo:'bg-success', medio:'bg-warning text-dark', alto:'bg-orange', critico:'bg-danger' }[riesgo] || 'bg-secondary';
    var distHtml = '';
    if (data.distribucion_clases) {
      distHtml = Object.keys(data.distribucion_clases).map(function(k) {
        var pct = (data.distribucion_clases[k] * 100).toFixed(1);
        return '<span class="badge ' + (badgeColor[k] || 'bg-secondary') + ' me-1">' + k + ': ' + pct + '%</span>';
      }).join('');
    }
    body.innerHTML =
      '<div class="mb-3">' +
        '<strong>Riesgo predicho:</strong> <span class="badge ' + badgeColor + ' fs-6">' + riesgo + '</span>' +
        ' <span class="text-muted ms-2">(Probabilidad: ' + prob + ')</span>' +
      '</div>' +
      '<div class="mb-3"><strong>Distribución:</strong><br>' + distHtml + '</div>' +
      '<div class="mb-3"><strong>Diagnóstico detallado:</strong><br><p class="mb-0">' + diag + '</p></div>' +
      (reco ? '<div class="mb-0"><strong>Recomendaciones:</strong><br><p class="mb-0">' + reco + '</p></div>' : '');
  } catch(e) {
    body.innerHTML = '<div class="alert alert-danger mb-0">Error de conexión: ' + e.message + '</div>';
  }
}

function exportarPdfFiltrado() {
  const riesgo   = document.getElementById('filtro-riesgo').value;
  const sexo     = document.getElementById('filtro-sexo').value;
  const critico  = document.getElementById('filtro-critico').checked;
  const busqueda = document.getElementById('busqueda').value.trim();

  let url = '/api/reportes/pdf/?';
  const params = [];
  if (riesgo)   params.push('riesgo=' + encodeURIComponent(riesgo));
  if (sexo)     params.push('sexo=' + encodeURIComponent(sexo));
  if (critico)  params.push('critico=true');
  if (busqueda) params.push('busqueda=' + encodeURIComponent(busqueda));
  url += params.length ? params.join('&') : '_=1';  // _=1 avoids empty ?

  descargarArchivo(url, 'reporte_pacientes.pdf');
}

document.addEventListener('DOMContentLoaded', () => cargarPacientes(1));
