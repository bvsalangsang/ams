# Generated by Django 5.1.7 on 2025-05-29 06:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('amsApp', '0009_manschedule'),
    ]

    operations = [
        migrations.AddField(
            model_name='manschedule',
            name='locationId',
            field=models.CharField(blank=True, max_length=5, null=True),
        ),
    ]
