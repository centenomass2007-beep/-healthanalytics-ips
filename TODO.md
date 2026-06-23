# TODO - Reto técnico ETL (Django + JS)

## Paso 1
- [x] Revisar implementación actual de frontend `etl.js` y backend `apps/etl/views.py`.

## Paso 2
- [ ] Corregir `frontend/static/js/etl.js` para enviar correctamente `FormData` y el header `X-CSRFToken`.
- [ ] Hacer que el frontend muestre errores detallados devueltos por el backend (JSON con `error/detalle/logs`).

## Paso 3
- [ ] Corregir backend `apps/etl/views.py` (vista `subir_dataset`) con `try/except` robusto y respuestas JSON consistentes y con códigos HTTP correctos.

## Paso 4
- [ ] Validar que la lectura de Excel funcione (si falta, instalar `openpyxl`).

## Paso 5
- [ ] Ejecutar pruebas manuales: subir `dataset_clinico.xlsx` y un CSV; verificar UI y errores.

