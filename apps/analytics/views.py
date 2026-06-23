from rest_framework.decorators import api_view, permission_classes
from apps.authentication.permissions import es_rol
from rest_framework.response import Response
from .services import (
    obtener_estadisticas_descriptivas, obtener_kpis,
    segmentacion_por_edad, segmentacion_por_diagnostico,
    distribucion_imc, tendencia_consultas_mensual,
    guardar_estadisticas_snapshot,
)

@api_view(['GET'])
@permission_classes([es_rol('administrador')])
def kpis(request):
    return Response(obtener_kpis())

@api_view(['GET'])
@permission_classes([es_rol('administrador')])
def estadisticas_descriptivas(request):
    return Response(obtener_estadisticas_descriptivas())

@api_view(['GET'])
@permission_classes([es_rol('administrador')])
def segmentacion(request):
    return Response({
        'por_edad': segmentacion_por_edad(),
        'por_diagnostico': segmentacion_por_diagnostico(),
        'por_imc': distribucion_imc(),
    })

@api_view(['GET'])
@permission_classes([es_rol('administrador')])
def tendencias(request):
    return Response({'consultas_mensuales': tendencia_consultas_mensual()})

@api_view(['POST'])
@permission_classes([es_rol('administrador')])
def generar_snapshot(request):
    snap = guardar_estadisticas_snapshot()
    return Response({'mensaje': 'Snapshot guardado', 'id': snap.id})
