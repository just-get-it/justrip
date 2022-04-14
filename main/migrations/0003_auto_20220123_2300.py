# Generated by Django 2.0 on 2022-01-23 23:00

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0002_auto_20220121_1816'),
    ]

    operations = [
        migrations.CreateModel(
            name='CouponType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
            ],
        ),
        migrations.AddField(
            model_name='coupon',
            name='coupon_type',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='main.CouponType'),
        ),
    ]
