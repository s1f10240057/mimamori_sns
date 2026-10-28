from datetime import timedelta
from unittest import mock

from celery.exceptions import Retry
from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase
from django.utils import timezone

from .models import NotificationSetting
from .tasks import dispatch_notifications, send_notification_mail

User = get_user_model()


def make_setting(username="alice", email="alice@example.com", **kwargs):
    user = User(email=email, account_id=username)
    user.set_password("pass")
    user.save()
    defaults = {
        "notify_at": timezone.now() - timedelta(minutes=1),
        "enabled": True,
        "task_ended": None,
    }
    defaults.update(kwargs)
    return NotificationSetting.objects.create(user=user, **defaults)


@mock.patch("notifications.tasks.send_notification_mail.delay") 
class DispatchNotificationsTests(TestCase):
    def test_sends_when_notify_time_has_passed(self, mock_delay):
        s = make_setting()

        dispatch_notifications()

        mock_delay.assert_called_once_with(s.user_id)
        s.refresh_from_db()
        self.assertIsNotNone(s.sent_at)

    def test_sends_when_notify_time_is_overdue_by_days(self, mock_delay):
        s = make_setting(notify_at=timezone.now() - timedelta(days=3))

        dispatch_notifications()

        mock_delay.assert_called_once_with(s.user_id)

    def test_does_not_send_before_notify_time(self, mock_delay):
        s = make_setting(notify_at=timezone.now() + timedelta(hours=1))

        dispatch_notifications()

        mock_delay.assert_not_called()
        s.refresh_from_db()
        self.assertIsNone(s.sent_at)

    def test_does_not_send_when_already_sent(self, mock_delay):
        sent = timezone.now() - timedelta(hours=1)
        s = make_setting(sent_at=sent)

        dispatch_notifications()

        mock_delay.assert_not_called()
        s.refresh_from_db()
        self.assertEqual(s.sent_at, sent)

    def test_does_not_send_when_disabled(self, mock_delay):
        make_setting(enabled=False)

        dispatch_notifications()

        mock_delay.assert_not_called()

    def test_does_not_send_when_task_ended(self, mock_delay):
        make_setting(task_ended=True)

        dispatch_notifications()

        mock_delay.assert_not_called()

    def test_second_run_does_not_send_again(self, mock_delay):
        make_setting()

        dispatch_notifications()
        dispatch_notifications()

        self.assertEqual(mock_delay.call_count, 1)

    def test_only_due_settings_are_sent(self, mock_delay):
        due = make_setting(username="due")
        make_setting(
            username="future",
            email="future@example.com",
            notify_at=timezone.now() + timedelta(hours=1),
        )

        dispatch_notifications()

        mock_delay.assert_called_once_with(due.user_id)

    def test_skips_when_claimed_by_another_worker_after_query(self, mock_delay):
        """targets取得後に別ワーカーが先に sent_at を更新した場合を再現する。"""
        s = make_setting()

        real_filter = NotificationSetting.objects.filter
        calls = {"n": 0}

        def filter_then_steal(*args, **kwargs):
            qs = real_filter(*args, **kwargs)
            calls["n"] += 1
            if calls["n"] == 1:
                list(qs)
                NotificationSetting.objects.filter(pk=s.pk).update(
                    sent_at=timezone.now()
                )
            return qs

        with mock.patch.object(
            NotificationSetting.objects, "filter", side_effect=filter_then_steal
        ):
            dispatch_notifications()

        mock_delay.assert_not_called()


class SendNotificationMailTests(TestCase):
    def test_sends_mail_to_user(self):
        s = make_setting()

        send_notification_mail(s.user_id)

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["alice@example.com"])
        self.assertIn("alice", mail.outbox[0].body)

    def test_skips_when_user_has_no_email(self):
        s = make_setting(email="")

        send_notification_mail(s.user_id)

        self.assertEqual(len(mail.outbox), 0)

    def test_retries_when_send_fails(self):
        s = make_setting()

        with mock.patch(
            "notifications.tasks.send_mail", side_effect=OSError("smtp down")  # "app" は実際のアプリ名に置き換え
        ), mock.patch.object(
            send_notification_mail, "retry", side_effect=Retry()
        ) as mock_retry:
            with self.assertRaises(Retry):
                send_notification_mail(s.user_id)

        mock_retry.assert_called_once()

    def test_raises_when_user_does_not_exist(self):
        with self.assertRaises(User.DoesNotExist):
            send_notification_mail(999999)


class DispatchToMailIntegrationTests(TestCase):
    def test_dispatch_sends_mail_in_eager_mode(self):
        from django.test import override_settings

        s = make_setting()

        with override_settings(
            CELERY_TASK_ALWAYS_EAGER=True, CELERY_TASK_EAGER_PROPAGATES=True
        ):

            dispatch_notifications.apply()

        s.refresh_from_db()
        self.assertIsNotNone(s.sent_at)