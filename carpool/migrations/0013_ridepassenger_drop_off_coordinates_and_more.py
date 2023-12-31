# Generated by Django 4.2.7 on 2023-12-03 02:53

import django.contrib.gis.db.models.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('carpool', '0012_remove_user_cover_photo_url_remove_user_photo_url'),
    ]

    operations = [
        migrations.AddField(
            model_name='ridepassenger',
            name='drop_off_coordinates',
            field=django.contrib.gis.db.models.fields.PointField(null=True, srid=4326),
        ),
        migrations.AddField(
            model_name='ridepassenger',
            name='drop_off_location',
            field=models.CharField(max_length=200, null=True),
        ),
        migrations.AddField(
            model_name='ridepassenger',
            name='pickup_coordinates',
            field=django.contrib.gis.db.models.fields.PointField(null=True, srid=4326),
        ),
        migrations.AddField(
            model_name='ridepassenger',
            name='pickup_location',
            field=models.CharField(max_length=200, null=True),
        ),
        migrations.AddField(
            model_name='ridepassenger',
            name='pickup_time',
            field=models.DateTimeField(null=True),
        ),
    ]
