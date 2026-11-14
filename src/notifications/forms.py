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

        labels = {
            "receive_user": "送る相手",
            "notify_at": "通知する日時",
            "enabled": "enabled",
            "task_theme": "写真のお題",
        }

        widgets = {
            "notify_at": forms.DateTimeInput(
                attrs={"type": "datetime-local"},
                format="%Y-%m-%dT%H:%M",
            ),
        }


class WeeklyNotificationRuleForm(ReceiverFieldMixin, forms.ModelForm):
    weekdays = forms.MultipleChoiceField(
        choices=WeeklyNotificationRule.Weekday.choices,
        widget=forms.CheckboxSelectMultiple(attrs={"class": "ns-weekday-checkbox"}),
        label="曜日",
        required=True,
        error_messages={"required": "曜日を1つ以上選択してください。"},
    )

    class Meta:
        model = WeeklyNotificationRule
        fields = ["receive_user", "notify_time", "task_theme", "enabled"]
        labels = {
            "receive_user": "送る相手",
            "notify_time": "通知する時間",
            "task_theme": "写真のお題",
            "enabled": "有効にする",
        }
        widgets = {
            "notify_time": forms.TimeInput(attrs={"type": "time"}, format="%H:%M"),
            "task_theme": forms.TextInput(attrs={"placeholder": "例: 朝ごはん、散歩の写真など"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields["weekdays"].initial = [str(self.instance.weekday)]