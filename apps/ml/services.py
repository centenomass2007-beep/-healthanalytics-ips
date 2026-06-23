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


def predecir_paciente(paciente_id: int, modelo_id: int = None) -> dict:
    """Predice riesgo para un paciente específico cargando el modelo desde el disco."""
    from apps.etl.models import Paciente as P
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

    return {
        'paciente_id': paciente_id,
        'riesgo_predicho': riesgo,
        'probabilidad': probabilidad,
        'distribucion_clases': dict(zip(le.classes_, proba.tolist())),
    }
