# Generated by Django 4.2.7 on 2023-12-02 21:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('carpool', '0010_user_cover_photo_url_user_photo_url'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='cover_photo_base64',
            field=models.TextField(null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='profile_photo_base64',
            field=models.TextField(null=True),
        ),
    ]
