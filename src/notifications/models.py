from django.conf import settings
from django.db import models

from mimamori.models import Photo


class WeeklyNotificationRule(models.Model):
    class Weekday(models.IntegerChoices):
        MON = 0, "月"
        TUE = 1, "火"
        WED = 2, "水"
        THU = 3, "木"
        FRI = 4, "金"
        SAT = 5, "土"
        SUN = 6, "日"

    created_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="created_rules",
    )
    receive_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="received_rules",
    )
    weekday = models.IntegerField(choices=Weekday.choices)
    notify_time = models.TimeField()
    enabled = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["created_user", "receive_user", "weekday"],
                name="uniq_rule_creator_receiver_weekday",
            )
        ]


class NotificationSetting(models.Model):
    created_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="created_notifications",
    )
    receive_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="received_notifications",
    )
    rule = models.ForeignKey(
        WeeklyNotificationRule,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="occurrences",
    )
    date = models.DateField(null=True, blank=True)

    task_ended = models.ForeignKey(
        Photo,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="notification_settings",
    )

    skipped_at = models.DateTimeField(null=True, blank=True)

    # models.BooleanField(default=False)
    task_theme = models.CharField(max_length=20, blank=True, default="")
    enabled = models.BooleanField(default=True)
    notify_at = models.DateTimeField(db_index=True)
    sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["rule", "date"], name="uniq_rule_date")
        ]