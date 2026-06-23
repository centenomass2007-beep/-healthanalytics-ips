import os
from django.conf import settings
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes
from .models import Paciente, HistorialETL
from .serializers import PacienteSerializer, HistorialETLSerializer
from .etl_engine import ejecutar_etl


class PacienteViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Lista y detalle de pacientes procesados por el ETL.
    Soporta filtrado por riesgo, sexo y estado crítico.
    """
    queryset = Paciente.objects.all()
    serializer_class = PacienteSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['pacientes'],
        parameters=[
            OpenApiParameter('riesgo', OpenApiTypes.STR,
                             description='Filtrar por nivel de riesgo: bajo, medio, alto, critico'),
            OpenApiParameter('sexo', OpenApiTypes.STR,
                             description='Filtrar por sexo: M, F'),
            OpenApiParameter('critico', OpenApiTypes.STR,
                             description='Solo pacientes críticos: true'),
        ],
        summary='Listar pacientes',
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        qs = super().get_queryset()
        riesgo  = self.request.query_params.get('riesgo')
        critico = self.request.query_params.get('critico')
        sexo    = self.request.query_params.get('sexo')
        if riesgo:           qs = qs.filter(riesgo_enfermedad=riesgo)
        if critico == 'true': qs = qs.filter(es_critico=True)
        if sexo:             qs = qs.filter(sexo=sexo)
        return qs


@extend_schema(
    tags=['etl'],
    summary='Ejecutar proceso ETL',
    description='Ejecuta Extract → Transform → Load sobre el dataset clínico almacenado en el servidor.',
    responses={200: HistorialETLSerializer},
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def ejecutar_etl_view(request):
    filepath = str(settings.BASE_DIR / 'datasets' / 'dataset_clinico.xlsx')
    if not os.path.exists(filepath):
        # Intentar con .csv
        filepath_csv = str(settings.BASE_DIR / 'datasets' / 'dataset_clinico.csv')
        if os.path.exists(filepath_csv):
            filepath = filepath_csv
        else:
            return Response(
                {'error': 'Dataset no encontrado. Sube un archivo primero usando /api/etl/upload/'},
                status=status.HTTP_404_NOT_FOUND
            )
    historial = ejecutar_etl(filepath, usuario=request.user)
    return Response(HistorialETLSerializer(historial).data)


@extend_schema(
    tags=['etl'],
    summary='Subir dataset y ejecutar ETL',
    description='Sube un archivo CSV o Excel. El proceso ETL se ejecuta automáticamente.',
    responses={200: HistorialETLSerializer},
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser])
def subir_dataset(request):
    try:
        archivo = request.FILES.get('archivo')
        if not archivo:
            return Response({'error': 'No se envió archivo'}, status=status.HTTP_400_BAD_REQUEST)

        os.makedirs(settings.DATASETS_DIR, exist_ok=True)
        ext = os.path.splitext(archivo.name)[1].lower()
        if ext not in ['.csv', '.xlsx', '.xls']:
            return Response(
                {'error': 'Formato no soportado. Use CSV o Excel (.csv, .xlsx, .xls)'},
                status=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
            )

        destino = os.path.join(settings.DATASETS_DIR, f'dataset_clinico{ext}')
        with open(destino, 'wb') as f:
            for chunk in archivo.chunks():
                f.write(chunk)

        historial = ejecutar_etl(destino, usuario=request.user)
        data = HistorialETLSerializer(historial).data

        if historial.estado == 'error':
            # En caso de error de ETL, devolver 400/422 para que el frontend sepa que falló.
            return Response(data, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

        return Response(data, status=status.HTTP_200_OK)

    except Exception as e:
        # Intentar devolver detalle estructurado al frontend
        detalle = str(e)
        error_tipo = e.__class__.__name__
        return Response(
            {
                'error': 'Fallo al subir o procesar el archivo',
                'detalle': detalle,
                'tipo': error_tipo,
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )



@extend_schema(
    tags=['etl'],
    summary='Historial de ejecuciones ETL',
    responses={200: HistorialETLSerializer(many=True)},
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def historial_etl(request):
    registros = HistorialETL.objects.all()[:20]
    return Response(HistorialETLSerializer(registros, many=True).data)
