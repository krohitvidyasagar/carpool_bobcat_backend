# Generated by Django 4.2.7 on 2023-12-01 21:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('carpool', '0008_message'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='from_location',
            field=models.CharField(max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='speaks',
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='studies',
            field=models.CharField(max_length=100, null=True),
        ),
    ]
