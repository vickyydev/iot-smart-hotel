# Generated by Django 3.2.25 on 2024-11-19 15:19

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('hotel', '0002_auto_20241119_1513'),
    ]

    operations = [
        migrations.AlterField(
            model_name='roomdevice',
            name='room',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='devices', to='hotel.room'),
        ),
    ]