# Generated by Django 4.2.7 on 2023-12-01 02:25

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('carpool', '0006_remove_riderreview_rider'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='RiderReview',
            new_name='DriverReview',
        ),
        migrations.AlterModelTable(
            name='driverreview',
            table='driver_review',
        ),
    ]
