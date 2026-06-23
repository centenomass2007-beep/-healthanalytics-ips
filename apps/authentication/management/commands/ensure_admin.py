from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()

USUARIOS = [
    {'username': 'admin',    'password': 'admin123',    'rol': 'administrador', 'is_superuser': True},
    {'username': 'medico',   'password': 'medico123',   'rol': 'medico',        'is_superuser': False},
    {'username': 'analista', 'password': 'analista123', 'rol': 'analista',      'is_superuser': False},
]


class Command(BaseCommand):
    help = 'Crea usuarios por defecto (admin, medico) si no existen'

    def handle(self, *args, **options):
        for u in USUARIOS:
            if User.objects.filter(username=u['username']).exists():
                self.stdout.write(self.style.WARNING(f'Usuario "{u["username"]}" ya existe, se omite'))
                continue
            if u['is_superuser']:
                User.objects.create_superuser(
                    username=u['username'],
                    email=f'{u["username"]}@example.com',
                    password=u['password'],
                    rol=u['rol'],
                )
            else:
                User.objects.create_user(
                    username=u['username'],
                    email=f'{u["username"]}@example.com',
                    password=u['password'],
                    rol=u['rol'],
                )
            self.stdout.write(self.style.SUCCESS(f'Usuario "{u["username"]}" creado (password: {u["password"]})'))
