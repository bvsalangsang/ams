# Generated by Django 5.1.7 on 2025-05-27 08:42

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('amsApp', '0006_manevent_maneventtype_manlocation_manlocationdet_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='manevent',
            old_name='eventType',
            new_name='eventTypeNo',
        ),
    ]
