from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from usuarios.models import Persona, Empleado, Roles, Permiso, Residentes
from comunidad.models import Unidad, ResidentesUnidad, Evento, Notificacion
from finanzas.models import Expensa, Pago
from economia.models import Gastos, Multa
from mantenimiento.models import AreaComun, Reserva
import datetime

User = get_user_model()

class Command(BaseCommand):
    help = 'Crea datos de prueba para el sistema'

    def handle(self, *args, **options):
        self.stdout.write('Creando datos de prueba...')
        
        # Crear roles
        rol_admin, created = Roles.objects.get_or_create(nombre='Administrador')
        if created:
            self.stdout.write(self.style.SUCCESS('Rol Administrador creado'))
        
        rol_residente, created = Roles.objects.get_or_create(nombre='Residente')
        if created:
            self.stdout.write(self.style.SUCCESS('Rol Residente creado'))

        # Crear permisos
        permisos_data = [
            'Gestionar usuarios',
            'Gestionar residentes',
            'Gestionar unidades',
            'Gestionar finanzas',
            'Gestionar mantenimiento',
            'Ver reportes',
            'Crear reservas',
            'Crear reclamos'
        ]
        
        for permiso_desc in permisos_data:
            permiso, created = Permiso.objects.get_or_create(descripcion=permiso_desc)
            if created:
                self.stdout.write(self.style.SUCCESS(f'Permiso {permiso_desc} creado'))

        # Crear persona para el administrador
        persona_admin, created = Persona.objects.get_or_create(
            nombre='Administrador del Sistema',
            defaults={
                'email': 'admin@sistema.com',
                'telefono': '123456789'
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('Persona Administrador creada'))

        # Obtener el usuario actual (tu superusuario)
        try:
            usuario_actual = User.objects.get(username='jael')
            
            # Crear empleado con cargo de administrador
            empleado_admin, created = Empleado.objects.get_or_create(
                usuario=usuario_actual,
                defaults={
                    'persona': persona_admin,
                    'cargo': 'Administrador'
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS('Empleado Administrador creado'))
            else:
                # Actualizar el cargo si ya existe
                empleado_admin.cargo = 'Administrador'
                empleado_admin.save()
                self.stdout.write(self.style.SUCCESS('Cargo de empleado actualizado a Administrador'))
                
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR('Usuario "jael" no encontrado. Crea un superusuario primero.'))

        # Crear unidades de prueba
        unidades_data = [
            {'numero_casa': 'A-101', 'metros_cuadrados': 85.5, 'cantidad_residentes': 3, 'cantidad_mascotas': 1, 'cantidad_vehiculos': 2},
            {'numero_casa': 'A-102', 'metros_cuadrados': 95.0, 'cantidad_residentes': 4, 'cantidad_mascotas': 0, 'cantidad_vehiculos': 1},
            {'numero_casa': 'B-201', 'metros_cuadrados': 75.0, 'cantidad_residentes': 2, 'cantidad_mascotas': 2, 'cantidad_vehiculos': 1},
        ]
        
        for unidad_data in unidades_data:
            unidad, created = Unidad.objects.get_or_create(
                numero_casa=unidad_data['numero_casa'],
                defaults=unidad_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Unidad {unidad_data["numero_casa"]} creada'))

        # Crear residentes de prueba
        residentes_data = [
            {'nombre': 'Juan Pérez', 'email': 'juan@email.com', 'telefono': '111111111'},
            {'nombre': 'María García', 'email': 'maria@email.com', 'telefono': '222222222'},
            {'nombre': 'Carlos López', 'email': 'carlos@email.com', 'telefono': '333333333'},
        ]
        
        for i, residente_data in enumerate(residentes_data):
            persona, created = Persona.objects.get_or_create(
                email=residente_data['email'],
                defaults=residente_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Persona {residente_data["nombre"]} creada'))
            
            # Crear usuario para el residente
            username = f'residente{i+1}'
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': residente_data['email'],
                    'first_name': residente_data['nombre'].split()[0],
                    'last_name': residente_data['nombre'].split()[1] if len(residente_data['nombre'].split()) > 1 else '',
                }
            )
            if created:
                user.set_password('password123')
                user.save()
                self.stdout.write(self.style.SUCCESS(f'Usuario {username} creado'))
            
            # Crear residente
            residente, created = Residentes.objects.get_or_create(
                persona=persona,
                defaults={'usuario': user}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Residente {residente_data["nombre"]} creado'))
            
            # Asociar residente con unidad
            unidad = Unidad.objects.get(numero_casa=unidades_data[i]['numero_casa'])
            residente_unidad, created = ResidentesUnidad.objects.get_or_create(
                id_residente=residente,
                id_unidad=unidad,
                defaults={
                    'rol_en_unidad': 'propietario',
                    'fecha_inicio': datetime.date.today(),
                    'estado': True
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Residente {residente_data["nombre"]} asociado a unidad {unidad.numero_casa}'))

        # Crear áreas comunes
        areas_data = [
            {'nombre': 'Gimnasio', 'tipo': 'Deportivo', 'descripcion': 'Gimnasio equipado con máquinas de ejercicio'},
            {'nombre': 'Salón de Eventos', 'tipo': 'Social', 'descripcion': 'Salón para fiestas y reuniones'},
            {'nombre': 'Piscina', 'tipo': 'Recreativo', 'descripcion': 'Piscina comunitaria'},
        ]
        
        for area_data in areas_data:
            area, created = AreaComun.objects.get_or_create(
                nombre=area_data['nombre'],
                defaults=area_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Área común {area_data["nombre"]} creada'))

        # Crear eventos de prueba
        eventos_data = [
            {'titulo': 'Asamblea General', 'descripcion': 'Asamblea general de propietarios', 'fecha': datetime.datetime.now() + datetime.timedelta(days=7)},
            {'titulo': 'Fiesta de Navidad', 'descripcion': 'Celebración navideña comunitaria', 'fecha': datetime.datetime.now() + datetime.timedelta(days=30)},
        ]
        
        for evento_data in eventos_data:
            evento, created = Evento.objects.get_or_create(
                titulo=evento_data['titulo'],
                defaults=evento_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Evento {evento_data["titulo"]} creado'))

        # Crear notificaciones de prueba
        notificaciones_data = [
            {'titulo': 'Mantenimiento de Ascensores', 'contenido': 'Se realizará mantenimiento preventivo de ascensores el próximo lunes', 'tipo': 'Mantenimiento'},
            {'titulo': 'Nuevo Reglamento', 'contenido': 'Se ha actualizado el reglamento de mascotas', 'tipo': 'Reglamento'},
        ]
        
        for notif_data in notificaciones_data:
            notif_data['fecha'] = datetime.datetime.now()
            notificacion, created = Notificacion.objects.get_or_create(
                titulo=notif_data['titulo'],
                defaults=notif_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Notificación {notif_data["titulo"]} creada'))

        # Crear expensas de prueba
        expensas_data = [
            {'descripcion': 'Mantenimiento General Enero', 'monto': 150.00, 'fecha_emision': datetime.date.today(), 'fecha_vencimiento': datetime.date.today() + datetime.timedelta(days=15)},
            {'descripcion': 'Servicios Básicos Enero', 'monto': 200.00, 'fecha_emision': datetime.date.today(), 'fecha_vencimiento': datetime.date.today() + datetime.timedelta(days=15)},
        ]
        
        for expensa_data in expensas_data:
            expensa, created = Expensa.objects.get_or_create(
                descripcion=expensa_data['descripcion'],
                defaults=expensa_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Expensa {expensa_data["descripcion"]} creada'))

        # Crear gastos de prueba
        gastos_data = [
            {'monto': 500.00, 'descripcion': 'Mantenimiento de jardines', 'fecha_hora': datetime.datetime.now()},
            {'monto': 300.00, 'descripcion': 'Limpieza de áreas comunes', 'fecha_hora': datetime.datetime.now()},
        ]
        
        for gasto_data in gastos_data:
            gasto, created = Gastos.objects.get_or_create(
                descripcion=gasto_data['descripcion'],
                defaults=gasto_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Gasto {gasto_data["descripcion"]} creado'))

        self.stdout.write(self.style.SUCCESS('¡Datos de prueba creados exitosamente!'))
        self.stdout.write('Usuarios de prueba:')
        self.stdout.write('- admin: jael (Administrador)')
        self.stdout.write('- residente1: residente1 (Residente)')
        self.stdout.write('- residente2: residente2 (Residente)')
        self.stdout.write('- residente3: residente3 (Residente)')
        self.stdout.write('Contraseña para todos: password123')
