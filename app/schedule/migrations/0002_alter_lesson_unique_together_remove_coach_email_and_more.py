# Generated by Django 4.1.13 on 2024-10-05 14:49

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('schedule', '0001_initial'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='lesson',
            unique_together=set(),
        ),
        migrations.RemoveField(
            model_name='coach',
            name='email',
        ),
        migrations.RemoveField(
            model_name='coach',
            name='end_date',
        ),
        migrations.RemoveField(
            model_name='coach',
            name='first_name',
        ),
        migrations.RemoveField(
            model_name='coach',
            name='last_name',
        ),
        migrations.RemoveField(
            model_name='coach',
            name='phone_number',
        ),
        migrations.RemoveField(
            model_name='coach',
            name='start_date',
        ),
        migrations.AddField(
            model_name='coach',
            name='department',
            field=models.CharField(default='Surfing', max_length=100),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='coach',
            name='is_surfcoach',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='coach',
            name='user',
            field=models.OneToOneField(default=1, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='lesson',
            name='booking',
            field=models.CharField(choices=[('3 Surfers', '3 Surfers'), ('Rapture', 'Rapture')], default='3 Surfers', max_length=50),
        ),
        migrations.AddField(
            model_name='lesson',
            name='meeting_point',
            field=models.CharField(choices=[('SCHOOL', 'SCHOOL'), ('RATURE CAMP', 'RATURE CAMP')], default='SCHOOL', max_length=50),
        ),
        migrations.AlterField(
            model_name='coach',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterUniqueTogether(
            name='lesson',
            unique_together={('booking', 'location', 'type_of_lesson', 'date', 'time')},
        ),
        migrations.RemoveField(
            model_name='lesson',
            name='coach',
        ),
        migrations.AddField(
            model_name='lesson',
            name='coach',
            field=models.ManyToManyField(to='schedule.coach'),
        ),
    ]