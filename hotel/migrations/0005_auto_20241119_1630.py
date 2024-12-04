# Generated by Django 3.2.25 on 2024-11-19 16:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hotel', '0004_auto_20241119_1616'),
    ]

    operations = [
        migrations.AlterField(
            model_name='accontrol',
            name='mode',
            field=models.CharField(choices=[('COOL', 'Cooling'), ('HEAT', 'Heating'), ('FAN', 'Fan Only'), ('AUTO', 'Automatic'), ('OFF', 'Off')], default='OFF', max_length=20),
        ),
        migrations.AlterField(
            model_name='accontrol',
            name='temperature',
            field=models.FloatField(default=24.0),
        ),
        migrations.AlterField(
            model_name='roomdevice',
            name='status',
            field=models.CharField(max_length=20),
        ),
    ]
