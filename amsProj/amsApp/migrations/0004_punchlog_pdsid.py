# Generated by Django 5.1.7 on 2025-05-15 08:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('amsApp', '0003_alter_punchlog_systemdatetime'),
    ]

    operations = [
        migrations.AddField(
            model_name='punchlog',
            name='pdsId',
            field=models.CharField(max_length=20, null=True),
        ),
    ]
