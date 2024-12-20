# Generated by Django 5.1.1 on 2024-12-16 20:40

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0015_remove_cables_ultima_advertencia'),
    ]

    operations = [
        migrations.CreateModel(
            name='ColaDispensa',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cable_referencia', models.IntegerField()),
                ('fecha_solicitud', models.DateTimeField(auto_now_add=True)),
                ('estado', models.CharField(default='pendiente', max_length=20)),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='tasks.usuarios')),
            ],
            options={
                'db_table': 'cola_dispensas',
            },
        ),
    ]