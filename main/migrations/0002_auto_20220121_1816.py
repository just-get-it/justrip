# Generated by Django 2.0 on 2022-01-21 18:16

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='trip',
            name='car_type',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='main.VehicalType'),
        ),
    ]
