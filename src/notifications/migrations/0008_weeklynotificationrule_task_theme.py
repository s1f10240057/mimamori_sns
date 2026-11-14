# Generated for adding task_theme to WeeklyNotificationRule

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0007_notificationsetting_skipped_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='weeklynotificationrule',
            name='task_theme',
            field=models.CharField(blank=True, default='', max_length=20),
        ),
    ]

