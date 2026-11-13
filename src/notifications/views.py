import json
import traceback
from zoneinfo import ZoneInfo

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from mimamori.views import get_pairs

from notifications.services import get_receivers

from .forms import NotificationSettingForm
from .models import NotificationSetting



@login_required
def notification_setting(request, pk=None):
    if request.user.role != "A":
        return HttpResponseForbidden("通知を設定できるのはロールAのみです。")

    if not get_receivers(request.user).exists():
        messages.error(request, "ペアが登録されていません。")
        return redirect("mimamori:index")

    setting = None
    if pk is not None:
        setting = get_object_or_404(
            NotificationSetting, pk=pk, created_user=request.user
        )

    form = NotificationSettingForm(
        request.POST or None, instance=setting, created_user=request.user
    )
    if request.method == "POST" and form.is_valid():
        s = form.save(commit=False)
        s.created_user = request.user
        if s.pk is None or {"notify_at", "receive_user"} & set(form.changed_data):
            s.sent_at = None
        s.save()
        return redirect("notifications:notification_settings")

    return render(request, "notifications/setting.html", {"form": form, "pairs":get_pairs(request.user)})

@login_required
@require_POST
def send_test_mail(request):
    user = request.user
    if not user.email:
        messages.error(request, "メールアドレスが登録されていません。")
        return redirect("notifications:notification_setting")
    try:
        send_mail(
            subject="【テスト】通知メール",
            message=f"{user.get_username()} さん、テストメールです。このメールが届けば設定は正常です。",
            from_email=None,
            recipient_list=[user.email],
        )
        messages.success(request, f"{user.email} にテストメールを送信しました。")
    except Exception as e:
        messages.error(request, f"送信に失敗しました: {e}")
    return redirect("notifications:notification_setting")

@login_required
@require_POST
def getNotificationAPI(request):
    try:
        data = json.loads(request.body.decode("utf-8"))
        target = data.get("target")
        qs = NotificationSetting.objects.filter(receive_user__account_id=target)

        # Aは自分が作った通知、Bは自分宛ての通知だけ
        if request.user.role == "A":
            qs = qs.filter(created_user=request.user)
        else:
            qs = qs.filter(receive_user=request.user)

        qs = qs.select_related("task_ended")
        tz = ZoneInfo("Asia/Tokyo")
        response_data = {
            "success": True,
            "notificationLst": [{
                "id": i.id,
                "notify_at": i.notify_at.astimezone(tz),
                "task_theme": i.task_theme,
                "task_ended": i.task_ended.image.url if i.task_ended else None,
                "skipped": i.skipped_at is not None,
                "done": i.task_ended_id is not None or i.skipped_at is not None,
            } for i in qs],
        }
    except Exception:
        traceback.print_exc()
        response_data = {"success": False}
    return JsonResponse(response_data)


def check_task(request):
    return render(request, "notifications/checkTask.html", {})


