# Generated by Django 5.1.7 on 2025-05-29 06:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('amsApp', '0008_remove_manevent_endafter_remove_manevent_endtime_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='ManSchedule',
            fields=[
                ('schedId', models.AutoField(primary_key=True, serialize=False)),
                ('eventNo', models.CharField(max_length=10)),
                ('startDate', models.DateField(blank=True, null=True)),
                ('endDate', models.DateField(blank=True, null=True)),
                ('startTime', models.CharField(max_length=8)),
                ('startGrace', models.CharField(max_length=8)),
                ('endTime', models.CharField(max_length=8)),
                ('endGrace', models.CharField(max_length=8)),
                ('recurrenceType', models.CharField(blank=True, max_length=20, null=True)),
                ('recurrenceDays', models.CharField(blank=True, max_length=20, null=True)),
                ('dateCreated', models.DateTimeField(auto_now_add=True, null=True)),
                ('isRecurring', models.CharField(default='N', max_length=1)),
                ('isActive', models.CharField(default='Y', max_length=1)),
            ],
            options={
                'db_table': 'schedule',
            },
        ),
    ]
