from rest_framework import serializers
from .models import ModeloML, PrediccionPaciente

class ModeloMLSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModeloML
        fields = '__all__'

class PrediccionSerializer(serializers.ModelSerializer):
    paciente_nombre = serializers.SerializerMethodField()
    def get_paciente_nombre(self, obj):
        return f"{obj.paciente.nombres} {obj.paciente.apellidos}"
    class Meta:
        model = PrediccionPaciente
        fields = '__all__'
