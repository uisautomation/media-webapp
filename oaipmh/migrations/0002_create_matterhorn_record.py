# Generated by Django 2.1.2 on 2018-11-21 21:09

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('oaipmh', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='MatterhornRecord',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.TextField(blank=True, help_text='Human-readable title')),
                ('description', models.TextField(blank=True, help_text='Human-readable description')),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='Creation time')),
                ('updated_at', models.DateTimeField(auto_now=True, help_text='Last update time')),
                ('record', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='matterhorn', to='oaipmh.Record')),
            ],
        ),
    ]
