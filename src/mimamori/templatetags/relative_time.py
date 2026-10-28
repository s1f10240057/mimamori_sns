from django import template
from django.utils import timezone

register = template.Library()


@register.filter
def ago(value):
    """日時を『何分前』『昨日』『3日前』の形式にする"""
    if not value:
        return ""

    now = timezone.localtime(timezone.now())
    value = timezone.localtime(value)
    seconds = (now - value).total_seconds()

    if seconds < 0:
        return "たった今"
    if seconds < 60:
        return "たった今"
    if seconds < 3600:
        return f"{int(seconds // 60)}分前"

    days = (now.date() - value.date()).days
    if days == 0:
        return f"{int(seconds // 3600)}時間前"
    if days == 1:
        return "昨日"
    if days < 30:
        return f"{days}日前"
    if days < 365:
        return f"{days // 30}か月前"
    return f"{days // 365}年前"