from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiExample
from drf_spectacular.types import OpenApiTypes
from .services import entrenar_modelo, predecir_paciente
from .models import ModeloML, PrediccionPaciente
from .serializers import ModeloMLSerializer, PrediccionSerializer


@extend_schema(
    tags=['ml'],
    summary='Entrenar modelo de ML',
    description='Entrena el algoritmo seleccionado con los datos clínicos limpios. '
                'Retorna métricas: Accuracy, Precision, Recall, F1-Score y Matriz de Confusión.',
    request={'application/json': {'type': 'object',
             'properties': {'algoritmo': {'type': 'string',
             'enum': ['random_forest', 'logistic_regression', 'decision_tree']}}}},
    responses={200: ModeloMLSerializer},
    examples=[OpenApiExample('Random Forest',
        value={'algoritmo': 'random_forest'}, request_only=True)],
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def entrenar(request):
    algoritmo = request.data.get('algoritmo', 'random_forest')
    try:
        modelo, metricas = entrenar_modelo(algoritmo)

        # Unificar respuesta esperada por el frontend
        # - status: success
        # - metrics: accuracy/precision/recall/f1_score
        # - matrix: dict con claves en mayúscula
        matrix = metricas.get('matrix')
        if not matrix:
            # compatibilidad con la estructura anterior
            cm = metricas.get('confusion_matrix') or metricas.get('confusion_matrix', [])
            clases = metricas.get('clases')
            if cm and clases:
                # cm esperada como lista NxN; se construye dict por etiqueta
                # Si el orden no coincide, al menos mantenemos el mismo mapeo por índice
                matrix = {
                    str(clases[i]).upper(): [int(v) for v in row]
                    for i, row in enumerate(cm)
                }

        unified = {
            'status': 'success',
            'metricas': {
                'accuracy': metricas.get('accuracy'),
                'precision': metricas.get('precision'),
                'recall': metricas.get('recall'),
                'f1_score': metricas.get('f1_score'),
            },
            'matrix': matrix or {},
        }

        return Response(unified | {
            'modelo': ModeloMLSerializer(modelo).data,
        })
    except ValueError as e:
        return Response({'status': 'error', 'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'status': 'error', 'error': f'Error entrenando modelo: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



@extend_schema(
    tags=['ml'],
    summary='Predecir riesgo de paciente',
    description='Predice el nivel de riesgo de enfermedad para un paciente específico.',
    request={'application/json': {'type': 'object',
             'properties': {'paciente_id': {'type': 'integer'}},
             'required': ['paciente_id']}},
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def predecir(request):
    paciente_id = request.data.get('paciente_id')
    if not paciente_id:
        return Response({'error': 'paciente_id requerido'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        resultado = predecir_paciente(int(paciente_id))
        return Response(resultado)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(tags=['ml'], summary='Listar modelos entrenados')
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def modelos_lista(request):
    modelos = ModeloML.objects.all()[:10]
    return Response(ModeloMLSerializer(modelos, many=True).data)


@extend_schema(tags=['ml'], summary='Listar predicciones realizadas')
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def predicciones_lista(request):
    preds = PrediccionPaciente.objects.all()[:50]
    return Response(PrediccionSerializer(preds, many=True).data)
