# Generated by Django 5.1.1 on 2024-11-13 14:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0013_alter_configuracioncable_unique_together'),
    ]

    operations = [
        migrations.AddField(
            model_name='registrodispensa',
            name='reproceso',
            field=models.BooleanField(default=False),
        ),
    ]
