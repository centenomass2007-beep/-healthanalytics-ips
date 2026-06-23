from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from apps.analytics.services import obtener_kpis, segmentacion_por_edad
from apps.analytics.services import distribucion_imc, segmentacion_por_diagnostico
from apps.etl.models import HistorialETL, Paciente
from apps.ml.models import ModeloML

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_kpis(request):
    kpis = obtener_kpis()
    ultimo_etl = HistorialETL.objects.first()
    modelo_activo = ModeloML.objects.filter(activo=True).first()
    return Response({
        'kpis': kpis,
        'ultimo_etl': {
            'fecha': ultimo_etl.fecha_ejecucion if ultimo_etl else None,
            'estado': ultimo_etl.estado if ultimo_etl else None,
            'registros': ultimo_etl.registros_limpios if ultimo_etl else 0,
        },
        'modelo_activo': {
            'nombre': modelo_activo.nombre if modelo_activo else None,
            'accuracy': modelo_activo.accuracy if modelo_activo else None,
        },
        'graficas': {
            'distribucion_riesgo': kpis.get('distribucion_riesgo', {}),
            'segmentacion_edad': segmentacion_por_edad(),
            'distribucion_imc': distribucion_imc(),
            'top_diagnosticos': segmentacion_por_diagnostico(),
        }
    })
