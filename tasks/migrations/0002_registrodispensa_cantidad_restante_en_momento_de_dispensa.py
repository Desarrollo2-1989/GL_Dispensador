# Generated by Django 5.1.1 on 2024-10-04 21:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='registrodispensa',
            name='cantidad_restante_en_momento_de_dispensa',
            field=models.IntegerField(null=True),
        ),
    ]