from rest_framework import serializers
from .models import Paciente, HistorialETL

class PacienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Paciente
        fields = '__all__'

class HistorialETLSerializer(serializers.ModelSerializer):
    usuario_nombre = serializers.CharField(source='usuario.username', read_only=True)
    class Meta:
        model = HistorialETL
        fields = '__all__'
