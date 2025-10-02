# Generated manually for notification system
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('comunidad', '0013_alter_reserva_area_alter_evento_areas_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='reserva',
            name='vista_por_admin',
            field=models.BooleanField(default=False),
        ),
    ]

