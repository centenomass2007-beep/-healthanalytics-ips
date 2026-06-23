from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import RegistroSerializer, UsuarioSerializer, CustomTokenSerializer

class LoginView(TokenObtainPairView):
    serializer_class = CustomTokenSerializer

@api_view(['POST'])
@permission_classes([AllowAny])
def registro(request):
    serializer = RegistroSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        return Response(UsuarioSerializer(user).data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def perfil(request):
    return Response(UsuarioSerializer(request.user).data)
