import json
import traceback
from zoneinfo import ZoneInfo

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.db import IntegrityError
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from mimamori.views import get_pairs

from notifications.services import generate_current_and_next_month, get_receivers

from .forms import NotificationSettingForm, WeeklyNotificationRuleForm
from .models import NotificationSetting, WeeklyNotificationRule



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
    if request.method == "POST" and "submit_single" in request.POST:
        if form.is_valid():
            s = form.save(commit=False)
            s.created_user = request.user
            if s.pk is None or {"notify_at", "receive_user"} & set(form.changed_data):
                s.sent_at = None
            s.save()
            messages.success(request, "タスクを保存しました。")
            return redirect("notifications:notification_settings")

    rule_form = WeeklyNotificationRuleForm(created_user=request.user)
    rules = WeeklyNotificationRule.objects.filter(
        created_user=request.user
    ).select_related("receive_user").order_by("weekday", "notify_time")

    return render(
        request,
        "notifications/setting.html",
        {
            "form": form,
            "rule_form": rule_form,
            "rules": rules,
            "pairs": get_pairs(request.user),
        },
    )


@login_required
@require_POST
def save_weekly_rule(request, pk=None):
    if request.user.role != "A":
        return HttpResponseForbidden("通知を設定できるのはロールAのみです。")

    instance = None
    if pk is not None:
        instance = get_object_or_404(
            WeeklyNotificationRule, pk=pk, created_user=request.user
        )

    rule_form = WeeklyNotificationRuleForm(
        request.POST, instance=instance, created_user=request.user
    )
    if rule_form.is_valid():
        selected_weekdays = rule_form.cleaned_data["weekdays"]
        receive_user = rule_form.cleaned_data["receive_user"]
        notify_time = rule_form.cleaned_data["notify_time"]
        task_theme = rule_form.cleaned_data.get("task_theme", "")
        enabled = rule_form.cleaned_data.get("enabled", True)

        saved_rules = []
        for w in selected_weekdays:
            rule, _ = WeeklyNotificationRule.objects.update_or_create(
                created_user=request.user,
                receive_user=receive_user,
                weekday=int(w),
                defaults={
                    "notify_time": notify_time,
                    "task_theme": task_theme,
                    "enabled": enabled,
                },
            )
            saved_rules.append(rule)

        enabled_rules = [r for r in saved_rules if r.enabled]
        if enabled_rules:
            generate_current_and_next_month(rules=enabled_rules)

        count = len(saved_rules)
        messages.success(request, f"{count}件の定期通知ルールを保存しました。")
    else:
        for field, errors in rule_form.errors.items():
            for error in errors:
                messages.error(request, error)

    return redirect("notifications:notification_settings")


@login_required
@require_POST
def delete_weekly_rule(request, pk):
    if request.user.role != "A":
        return HttpResponseForbidden("通知を設定できるのはロールAのみです。")

    rule = get_object_or_404(
        WeeklyNotificationRule, pk=pk, created_user=request.user
    )
    rule.occurrences.filter(sent_at__isnull=True).delete()
    rule.delete()
    messages.success(request, "定期通知ルールを削除しました。")
    return redirect("notifications:notification_settings")


@login_required
@require_POST
def toggle_weekly_rule(request, pk):
    if request.user.role != "A":
        return HttpResponseForbidden("通知を設定できるのはロールAのみです。")

    rule = get_object_or_404(
        WeeklyNotificationRule, pk=pk, created_user=request.user
    )
    rule.enabled = not rule.enabled
    rule.save()
    if rule.enabled:
        generate_current_and_next_month(rules=[rule])
        rule.occurrences.filter(sent_at__isnull=True).update(enabled=True)
        messages.success(request, "定期通知ルールを有効にしました。")
    else:
        rule.occurrences.filter(sent_at__isnull=True).update(enabled=False)
        messages.success(request, "定期通知ルールを無効にしました。")

    return redirect("notifications:notification_settings")

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


