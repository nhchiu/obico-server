# Generated by Django 2.2.27 on 2022-09-17 23:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0067_auto_20220915_1953'),
    ]

    operations = [
        migrations.RenameField(
            model_name='printevent',
            old_name='help_url',
            new_name='info_url',
        ),
        migrations.AddField(
            model_name='user',
            name='suppressed_printer_event_json',
            field=models.CharField(blank=True, max_length=2000, null=True),
        ),
    ]