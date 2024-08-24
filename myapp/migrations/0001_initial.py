# Generated by Django 5.0.7 on 2024-08-05 22:20

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Item',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=60)),
                ('size', models.CharField(max_length=3)),
                ('price', models.PositiveIntegerField()),
            ],
        ),
    ]
