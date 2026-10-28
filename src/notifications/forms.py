from django import forms
from django.utils import timezone

from .models import NotificationSetting, WeeklyNotificationRule
from .services import get_receivers


class ReceiverFieldMixin:
    """receive_user の選択肢を、作成者のペア(ロールB)に限定する。"""

    def __init__(self, *args, created_user, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["receive_user"].queryset = get_receivers(created_user)
        self.fields["receive_user"].label = "通知を送る相手"
        self.fields["receive_user"].empty_label = None


class NotificationSettingForm(ReceiverFieldMixin, forms.ModelForm):
    class Meta:
        model = NotificationSetting
        fields = ["receive_user", "notify_at", "enabled", "task_theme"]
        widgets = {
            "notify_at": forms.DateTimeInput(
                attrs={"type": "datetime-local"},
                format="%Y-%m-%dT%H:%M",
            ),
        }


class WeeklyNotificationRuleForm(ReceiverFieldMixin, forms.ModelForm):
    class Meta:
        model = WeeklyNotificationRule
        fields = ["receive_user", "weekday", "notify_time", "enabled"]
        widgets = {
            "notify_time": forms.TimeInput(attrs={"type": "time"}, format="%H:%M"),
        }