import calendar
from datetime import date, datetime

from django.db.models import Q
from django.utils import timezone

from .models import NotificationSetting, WeeklyNotificationRule
from django.contrib.auth import get_user_model
from mimamori.models import PairRelationship


def get_receivers(creator):
    User = get_user_model()
    partner_ids = set()
    for a_id, b_id in PairRelationship.objects.filter(
        Q(a_user=creator) | Q(b_user=creator)
    ).values_list("a_user_id", "b_user_id"):
        partner_ids.add(b_id if a_id == creator.pk else a_id)
    return User.objects.filter(pk__in=partner_ids, role="B")


def generate_for_month(year, month, rules=None):
    now = timezone.now()
    tz = timezone.get_current_timezone()
    last_day = calendar.monthrange(year, month)[1]
    rules = rules or WeeklyNotificationRule.objects.filter(enabled=True)

    new_rows = []
    for rule in rules:
        for day in range(1, last_day + 1):
            d = date(year, month, day)
            if d.weekday() != rule.weekday:
                continue
            notify_at = timezone.make_aware(
                datetime.combine(d, rule.notify_time), tz
            )
            if notify_at <= now:
                continue
            new_rows.append(
                NotificationSetting(
                    created_user_id=rule.created_user_id,
                    receive_user_id=rule.receive_user_id,
                    rule=rule,
                    date=d,
                    notify_at=notify_at,
                )
            )
    NotificationSetting.objects.bulk_create(new_rows, ignore_conflicts=True)
    return len(new_rows)


def generate_current_and_next_month(rules=None):
    today = timezone.localdate()
    generate_for_month(today.year, today.month, rules)
    ny, nm = (today.year + 1, 1) if today.month == 12 else (today.year, today.month + 1)
    generate_for_month(ny, nm, rules)