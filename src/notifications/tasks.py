from celery import shared_task
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.utils import timezone

from config import settings
from notifications.services import get_receivers

from .models import NotificationSetting


@shared_task
def dispatch_notifications():
    now = timezone.localtime()

    targets = NotificationSetting.objects.filter(
        enabled=True,
        task_ended=None,
        notify_at__lte=now,
        sent_at__isnull=True,
    )
    for s in targets:
        
        updated = (
            NotificationSetting.objects
            .filter(pk=s.pk, enabled=True, task_ended=None, sent_at__isnull=True)
            .update(sent_at=now)
        )
        # tasks.py の dispatch_notifications のループ内
        if updated:
            if get_receivers(s.created_user).filter(pk=s.receive_user_id).exists():
                send_notification_mail.delay(s.receive_user_id, s.id)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_notification_mail(self, user_id, task_id):
    user = get_user_model().objects.get(pk=user_id)
    if not user.email:
        return
    try:
        url = f"{settings.SITE_URL}/mimamori/doTask/{task_id}"
        send_mail(
            subject="タスクが届きました！！！",
            message=f"""{user.get_username()} さん、本日のタスクが届きました。
URL先から行うことができます。
URL: {url}""",
            from_email=None,
            recipient_list=[user.email],
        )
    except Exception as exc:
        raise self.retry(exc=exc)


@shared_task
def generate_monthly_notifications():
    from .services import generate_current_and_next_month
    generate_current_and_next_month()