from django.urls import path
from . import views

app_name = "notifications"

urlpatterns = [
    path("settings/", views.notification_setting, name="notification_settings"),
    path("settings/<int:pk>/", views.notification_setting, name="notification_setting_edit"),
    path("check_task/", views.check_task, name="check_task"),
    path("test-mail/", views.send_test_mail, name="send_test_mail"),
    path("getNotificationAPI/", views.getNotificationAPI, name="getNotification"),
]