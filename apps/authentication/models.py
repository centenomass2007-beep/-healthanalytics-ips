from django.contrib.auth.models import AbstractUser
from django.db import models

class Usuario(AbstractUser):
    ROL_CHOICES = [
        ('administrador', 'Administrador'),
        ('medico', 'Médico'),
        ('analista', 'Analista'),
    ]
    rol = models.CharField(max_length=20, choices=ROL_CHOICES, default='analista')
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'

    def __str__(self):
        return f"{self.username} ({self.get_rol_display()})"
