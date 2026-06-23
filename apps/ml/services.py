import os
import pickle
import numpy as np
import pandas as pd
from django.conf import settings
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import (accuracy_score, precision_score,
                             recall_score, f1_score, confusion_matrix)
from apps.etl.models import Paciente
from .models import ModeloML, PrediccionPaciente

FEATURES = ['edad', 'imc', 'glucosa', 'colesterol', 'presion_sistolica',
            'presion_diastolica', 'frecuencia_cardiaca', 'saturacion_oxigeno',
            'temperatura', 'fumador', 'consumo_alcohol', 'antecedentes_familiares']

ALGORITMOS = {
    'logistic_regression': LogisticRegression(max_iter=500, random_state=42),
    'decision_tree': DecisionTreeClassifier(max_depth=8, random_state=42),
    'random_forest': RandomForestClassifier(n_estimators=100, random_state=42),
}


def _preparar_dataset():
    qs = Paciente.objects.exclude(riesgo_enfermedad__isnull=True)
    df = pd.DataFrame(list(qs.values(*FEATURES, 'riesgo_enfermedad', 'id')))
    if df.empty or len(df) < 50:
        raise ValueError("Dataset insuficiente para entrenar (mínimo 50 registros)")

    # Booleanos a int
    for col in ['fumador', 'consumo_alcohol', 'antecedentes_familiares']:
        df[col] = df[col].astype(int)

    # Normalizar/limpiar valores faltantes
    X = df[FEATURES].copy()
    X = X.apply(pd.to_numeric, errors='coerce')
    X = X.fillna(df[FEATURES].median(numeric_only=True))

    # Etiquetas como string consistente
    le = LabelEncoder()
    y_raw = df['riesgo_enfermedad'].astype(str).fillna('bajo')
    y = le.fit_transform(y_raw)
    return X, y, le, df['id'].tolist()


def entrenar_modelo(algoritmo: str = 'random_forest') -> ModeloML:
    """Entrena el modelo seleccionado y persiste métricas."""
    if algoritmo not in ALGORITMOS:
        raise ValueError(f"Algoritmo '{algoritmo}' no soportado")

    X, y, le, ids = _preparar_dataset()
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y)

    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s = scaler.transform(X_test)

    clf = ALGORITMOS[algoritmo]

    # Nota: para RandomForest/DecisionTree el escalado no aporta y puede
    # empeorar en algunos escenarios. Usamos escalado solo para modelos
    # lineales.
    if algoritmo in ['logistic_regression']:
        X_train_use, X_test_use = X_train_s, X_test_s
    else:
        X_train_use, X_test_use = X_train, X_test

    clf.fit(X_train_use, y_train)
    y_pred = clf.predict(X_test_use)

    acc = round(float(accuracy_score(y_test, y_pred)), 4)
    prec = round(float(precision_score(y_test, y_pred, average='weighted', zero_division=0)), 4)
    rec = round(float(recall_score(y_test, y_pred, average='weighted', zero_division=0)), 4)
    f1 = round(float(f1_score(y_test, y_pred, average='weighted', zero_division=0)), 4)
    cm = confusion_matrix(y_test, y_pred).tolist()

    # Desactiva modelos anteriores del mismo tipo
    ModeloML.objects.filter(algoritmo=algoritmo).update(activo=False)

    modelo_obj = ModeloML.objects.create(
        nombre=f"{algoritmo.replace('_', ' ').title()} v{ModeloML.objects.count()+1}",
        algoritmo=algoritmo,
        accuracy=acc, precision=prec, recall=rec, f1_score=f1,
        matriz_confusion=cm,
        variables_predictoras=FEATURES,
        activo=True,
    )

    # Almacenar en disco usando pickle
    model_dir = os.path.join(settings.MEDIA_ROOT, 'models')
    os.makedirs(model_dir, exist_ok=True)

    clf_path = os.path.join(model_dir, f"modelo_{modelo_obj.id}_clf.pkl")
    scaler_path = os.path.join(model_dir, f"modelo_{modelo_obj.id}_scaler.pkl")
    le_path = os.path.join(model_dir, f"modelo_{modelo_obj.id}_le.pkl")

    with open(clf_path, 'wb') as f:
        pickle.dump(clf, f)
    with open(scaler_path, 'wb') as f:
        pickle.dump(scaler, f)
    with open(le_path, 'wb') as f:
        pickle.dump(le, f)

    # Almacena scaler y modelo en memoria por si acaso para la petición activa
    modelo_obj._clf = clf
    modelo_obj._scaler = scaler
    modelo_obj._le = le

    return modelo_obj, {'accuracy': acc, 'precision': prec, 'recall': rec,
                        'f1_score': f1, 'confusion_matrix': cm,
                        'clases': list(le.classes_)}


def _construir_diagnostico_y_recomendaciones(*, riesgo: str, probabilidad: float, paciente_features: dict) -> tuple[str, list[str]]:
    """Genera diagnóstico detallado y recomendaciones con heurísticas por variables.

    Nota: esto mejora la interpretación/explicación del resultado.
    """

    edad = paciente_features.get('edad')
    imc = paciente_features.get('imc')
    glucosa = paciente_features.get('glucosa')
    colesterol = paciente_features.get('colesterol')
    ps = paciente_features.get('presion_sistolica')
    pd = paciente_features.get('presion_diastolica')
    fc = paciente_features.get('frecuencia_cardiaca')
    spo2 = paciente_features.get('saturacion_oxigeno')
    temp = paciente_features.get('temperatura')
    fumador = bool(paciente_features.get('fumador'))
    alcohol = bool(paciente_features.get('consumo_alcohol'))
    antecedentes = bool(paciente_features.get('antecedentes_familiares'))

    # Señales (heurísticas) -> (texto_corto, severidad)
    señales: list[tuple[str, int]] = []

    if imc is not None:
        try:
            imc_v = float(imc)
            if imc_v >= 30:
                señales.append((f"IMC elevado ({imc_v:.1f}) sugiere obesidad.", 3))
            elif imc_v >= 25:
                señales.append((f"IMC en rango de sobrepeso ({imc_v:.1f}).", 2))
        except Exception:
            pass

    if glucosa is not None:
        try:
            g = float(glucosa)
            if g >= 126:
                señales.append((f"Glucosa alta (≥126): posible hiperglucemia.", 3))
            elif g >= 100:
                señales.append((f"Glucosa elevada (100–125): posible prediabetes.", 2))
        except Exception:
            pass

    if colesterol is not None:
        try:
            c = float(colesterol)
            if c >= 240:
                señales.append((f"Colesterol alto (≥240): riesgo cardiovascular.", 3))
            elif c >= 200:
                señales.append((f"Colesterol en rango alto (200–239).", 2))
        except Exception:
            pass

    if ps is not None and pd is not None:
        try:
            ps_v = float(ps)
            pd_v = float(pd)
            # Rangos simplificados
            if ps_v >= 180 or pd_v >= 120:
                señales.append(("Presión arterial muy elevada: requiere evaluación prioritaria.", 3))
            elif ps_v >= 140 or pd_v >= 90:
                señales.append(("Presión arterial elevada: controlar y vigilar complicaciones.", 2))
            elif ps_v >= 120 or pd_v >= 80:
                señales.append(("Presión arterial en rango alto-normal: educación y seguimiento.", 1))
        except Exception:
            pass

    if fc is not None:
        try:
            fc_v = float(fc)
            if fc_v >= 100:
                señales.append((f"Frecuencia cardiaca alta ({fc_v:.0f} lpm).", 2))
            elif fc_v < 50:
                señales.append((f"Frecuencia cardiaca baja ({fc_v:.0f} lpm).", 1))
        except Exception:
            pass

    if spo2 is not None:
        try:
            s = float(spo2)
            if s < 92:
                señales.append((f"Saturación de O2 baja ({s:.0f}%): alerta respiratoria.", 3))
            elif s < 95:
                señales.append((f"Saturación de O2 algo baja ({s:.0f}%).", 2))
        except Exception:
            pass

    if temp is not None:
        try:
            t = float(temp)
            if t >= 38:
                señales.append((f"Temperatura elevada ({t:.1f}°C): considerar proceso infeccioso.", 2))
        except Exception:
            pass

    if fumador:
        señales.append(("Tabaquismo: incrementa riesgo cardiovascular y respiratorio.", 2))

    if alcohol:
        señales.append(("Consumo de alcohol: evaluar cantidad/periodicidad y riesgos asociados.", 1))

    if antecedentes:
        señales.append(("Antecedentes familiares: mayor probabilidad basal.", 2))

    # Nivel de confianza
    # (Se asume que riesgo_predicho es una clase; la probabilidad refleja confianza del modelo)
    confianza = "alta" if probabilidad >= 0.65 else ("media" if probabilidad >= 0.5 else "baja")

    # Diagnóstico base según riesgo
    riesgo_norm = (riesgo or "").strip().lower()
    if riesgo_norm in ["alto", "high", "critico", "crítico", "critico/a", "criticoa", "grave"]:
        diagnostico = "Riesgo elevado de enfermedad." 
    elif riesgo_norm in ["medio", "med", "intermedio"]:
        diagnostico = "Riesgo intermedio de enfermedad: se recomienda control y prevención." 
    else:
        diagnostico = "Riesgo bajo de enfermedad." 

    if confianza == "baja":
        diagnostico += " La predicción tiene confianza limitada; considere complementar con evaluación clínica y controles." 
    elif confianza == "media":
        diagnostico += " La predicción tiene confianza moderada." 
    else:
        diagnostico += " La predicción tiene confianza alta." 

    # Añadir resumen por señales
    if señales:
        # Ordenar por severidad descendente
        señales_sorted = sorted(señales, key=lambda x: x[1], reverse=True)
        # Tomar top 4
        top = [s for s, _ in señales_sorted[:4]]
        diagnostico += "\n" + "Indicadores relevantes: " + " ".join(top)

    # Recomendaciones
    recomendaciones: list[str] = []

    # Reglas por señales + riesgo
    # Presión arterial
    if ps is not None and pd is not None:
        try:
            ps_v = float(ps); pd_v = float(pd)
            if ps_v >= 140 or pd_v >= 90:
                recomendaciones.append("Control de presión arterial: seguimiento con profesional y adhesión a tratamiento si aplica.")
                recomendaciones.append("Reducir sal en la dieta, actividad física regular y monitoreo domiciliario cuando sea posible.")
        except Exception:
            pass

    # Glucosa
    if glucosa is not None:
        try:
            g = float(glucosa)
            if g >= 100:
                recomendaciones.append("Evaluar metabolismo de glucosa: solicitud de HbA1c/curva y plan dietario/actividad.")
        except Exception:
            pass

    # Colesterol
    if colesterol is not None:
        try:
            c = float(colesterol)
            if c >= 200:
                recomendaciones.append("Perfil lipídico: revisar dieta (grasas saludables), actividad y considerar manejo farmacológico si lo indica el médico.")
        except Exception:
            pass

    # IMC
    if imc is not None:
        try:
            imc_v = float(imc)
            if imc_v >= 25:
                recomendaciones.append("Plan de nutrición y actividad para mejorar IMC (metas realistas y seguimiento profesional).")
        except Exception:
            pass

    # Oxigenación
    if spo2 is not None:
        try:
            s = float(spo2)
            if s < 95:
                recomendaciones.append("Si hay síntomas respiratorios, priorizar evaluación clínica; revisar causas y tratamiento indicado.")
        except Exception:
            pass

    # Tabaquismo
    if fumador:
        recomendaciones.append("Abandono del tabaco: programas de cesación y soporte. Es una de las intervenciones de mayor impacto.")

    # Antecedentes
    if antecedentes:
        recomendaciones.append("Con antecedentes familiares, intensificar prevención: chequeos periódicos y estilo de vida saludable.")

    # Si el riesgo es alto o confianza media/baja, añadir recomendación general
    if riesgo_norm in ["alto", "critico", "crítico", "grave"] or confianza != "alta":
        recomendaciones.append("Recomendación general: validar hallazgos con evaluación clínica completa y exámenes complementarios según criterio médico.")

    if not recomendaciones:
        recomendaciones.append("Mantener hábitos saludables y realizar controles periódicos según edad y factores de riesgo.")

    # Deduplicar preservando orden
    seen = set(); recs = []
    for r in recomendaciones:
        if r not in seen:
            seen.add(r); recs.append(r)

    return diagnostico, recs


def predecir_paciente(paciente_id: int, modelo_id: int = None) -> dict:
    """Predice riesgo para un paciente específico cargando el modelo desde el disco."""
    from apps.etl.models import Paciente as P


    # El modelo ETL define `id_paciente` (no `id`).
    # El frontend envía `paciente_id` como el ID clínico (id_paciente).
    try:
        paciente = P.objects.get(id_paciente=paciente_id)
    except P.DoesNotExist:
        # Fallback por compatibilidad con posibles implementaciones previas
        paciente = P.objects.get(id=paciente_id)


    datos = {f: getattr(paciente, f, 0) or 0 for f in FEATURES}
    for col in ['fumador', 'consumo_alcohol', 'antecedentes_familiares']:
        datos[col] = int(datos[col])

    X_input = pd.DataFrame([datos])[FEATURES]

    # Buscar el modelo
    if modelo_id:
        try:
            modelo_obj = ModeloML.objects.get(id=modelo_id)
        except ModeloML.DoesNotExist:
            raise ValueError(f"El modelo con ID {modelo_id} no existe.")
    else:
        modelo_obj = ModeloML.objects.filter(activo=True).first()
        if not modelo_obj:
            # Si no hay modelo entrenado, entrenamos uno por defecto
            modelo_obj, _ = entrenar_modelo('random_forest')

    # Intentar cargar desde el disco
    model_dir = os.path.join(settings.MEDIA_ROOT, 'models')
    clf_path = os.path.join(model_dir, f"modelo_{modelo_obj.id}_clf.pkl")
    scaler_path = os.path.join(model_dir, f"modelo_{modelo_obj.id}_scaler.pkl")
    le_path = os.path.join(model_dir, f"modelo_{modelo_obj.id}_le.pkl")

    if os.path.exists(clf_path) and os.path.exists(scaler_path) and os.path.exists(le_path):
        with open(clf_path, 'rb') as f:
            clf = pickle.load(f)
        with open(scaler_path, 'rb') as f:
            scaler = pickle.load(f)
        with open(le_path, 'rb') as f:
            le = pickle.load(f)
    else:
        # Si por algún motivo no están los archivos, forzamos re-entrenamiento
        modelo_obj, _ = entrenar_modelo(modelo_obj.algoritmo)
        clf_path = os.path.join(model_dir, f"modelo_{modelo_obj.id}_clf.pkl")
        scaler_path = os.path.join(model_dir, f"modelo_{modelo_obj.id}_scaler.pkl")
        le_path = os.path.join(model_dir, f"modelo_{modelo_obj.id}_le.pkl")
        with open(clf_path, 'rb') as f:
            clf = pickle.load(f)
        with open(scaler_path, 'rb') as f:
            scaler = pickle.load(f)
        with open(le_path, 'rb') as f:
            le = pickle.load(f)

    X_scaled = scaler.transform(X_input)

    proba = clf.predict_proba(X_scaled)[0]
    clase_idx = np.argmax(proba)
    riesgo = le.inverse_transform([clase_idx])[0]
    probabilidad = round(float(proba[clase_idx]), 4)

    PrediccionPaciente.objects.create(
        paciente=paciente,
        modelo=modelo_obj,
        probabilidad_riesgo=probabilidad,
        riesgo_predicho=riesgo,
    )

    diagnostico_detallado, recomendaciones = _construir_diagnostico_y_recomendaciones(
        riesgo=riesgo,
        probabilidad=probabilidad,
        paciente_features=datos,
    )

    return {
        'paciente_id': paciente_id,
        'riesgo_predicho': riesgo,
        'probabilidad': probabilidad,
        'diagnostico_detallado': diagnostico_detallado,
        'recomendaciones': recomendaciones,
        'distribucion_clases': dict(zip(le.classes_, proba.tolist())),
    }

