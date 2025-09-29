from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('usuarios', '0009_tipotarea_tareaempleado_evaluaciontarea_and_more'),
        ('comunidad', '0010_add_destinatarios_field'),
    ]

    operations = [
        # Invitado may exist with only nombre, ci, evento; add missing fields
        migrations.AddField(
            model_name='invitado',
            name='residente',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='invitados', to='usuarios.residentes'),
        ),
        migrations.AddField(
            model_name='invitado',
            name='tipo',
            field=models.CharField(choices=[('casual', 'Visita Casual'), ('evento', 'Invitado Evento')], default='casual', max_length=10),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='invitado',
            name='evento',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='comunidad.evento'),
        ),
        migrations.AddField(
            model_name='invitado',
            name='vehiculo_placa',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
        migrations.AddField(
            model_name='invitado',
            name='fecha_inicio',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='invitado',
            name='fecha_fin',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='invitado',
            name='activo',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='invitado',
            name='check_in_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='invitado',
            name='check_in_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='invitados_checkin', to='usuarios.usuario'),
        ),
        migrations.AddField(
            model_name='invitado',
            name='check_out_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='invitado',
            name='check_out_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='invitados_checkout', to='usuarios.usuario'),
        ),
        migrations.AddField(
            model_name='invitado',
            name='creado_en',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AddField(
            model_name='invitado',
            name='actualizado_en',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]




