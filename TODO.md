# TODO - Mejora predicción + diagnóstico detallado

## Paso 1: implementar lógica de diagnóstico y recomendaciones
- [x] Editar `apps/ml/services.py`
  - [x] Construir `diagnostico_detallado` según `riesgo_predicho`, `probabilidad` y valores de FEATURES del paciente
  - [x] Generar `recomendaciones` (lista) basada en heurísticas por feature
  - [x] Devolver estos campos en el dict del endpoint `predecir_paciente`

## Paso 2: actualizar UI
- [x] Editar `frontend/templates/ml/index.html`
  - [x] Agregar contenedor/estructura para mostrar diagnóstico y recomendaciones

## Paso 3: actualizar frontend JS
- [x] Editar `frontend/static/js/ml.js`
  - [x] Renderizar `diagnostico_detallado` y `recomendaciones` en `predecirPaciente()`


## Paso 4: validar
- [ ] Probar el endpoint `/api/ml/predecir/` y verificar que la respuesta incluya nuevos campos
- [ ] Probar la pantalla ML y verificar que se rendericen en UI

